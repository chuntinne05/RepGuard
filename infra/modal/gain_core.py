"""Bounded routing baselines; learners see only revealed training outcomes."""
from collections import Counter
import re
import numpy as np
from neural_core import means, inner_folds, ht_score

FAMILIES = ('Global', 'FactorRidge', 'SemanticRidge', 'TextRidge', 'DirectUtility')
PARAMS = {'Global': (0,), 'FactorRidge': (4., 16.), 'SemanticRidge': (1., 10.),
          'TextRidge': (1., 10.), 'DirectUtility': (.0001, .001)}


def terms(text):
    words = re.findall(r'[a-z][a-z0-9_]+', text.lower())
    return words + [a+' '+b for a,b in zip(words, words[1:])]


def text_features(train, test):
    counts = Counter(t for text in train for t in set(terms(text)))
    vocab = sorted(counts, key=lambda t: (-counts[t], t))[:4096]
    lookup = {t:i for i,t in enumerate(vocab)}
    idf = np.array([np.log((1+len(train))/(1+counts[t]))+1 for t in vocab])
    def transform(texts):
        x = np.zeros((len(texts),len(vocab)))
        for i,text in enumerate(texts):
            for t,n in Counter(terms(text)).items():
                if t in lookup:
                    x[i,lookup[t]] = (1+np.log(n))*idf[lookup[t]]
        return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
    return transform(train), transform(test), vocab


def center_features(train, test):
    center = train.mean(0)
    return train-center, test-center


def factor_design(agents):
    metadata = [a.rsplit('_',1) for a in agents]
    scaffolds = sorted({s for s,m in metadata})
    models = sorted({m for s,m in metadata})
    out = np.zeros((len(agents),1+len(models)+len(scaffolds)+len(agents)))
    out[:,0] = 1
    for a,(s,m) in enumerate(metadata):
        out[a,1+models.index(m)] = 1
        out[a,1+len(models)+scaffolds.index(s)] = 1
        out[a,1+len(models)+len(scaffolds)+a] = 1
    return out


def factor_scores(observed, agents, penalty):
    design = factor_design(agents)
    rows, cols = np.where(np.isfinite(observed))
    if not len(rows):
        raise ValueError('No observed labels')
    z = design[cols]
    lam = np.ones(z.shape[1]); lam[0] = 0; lam[-len(agents):] = penalty
    coef = np.linalg.solve(z.T@z+np.diag(lam), z.T@(observed[rows,cols]-.5))
    return .5 + design@coef


def ridge_predict(x, observed, xt, alpha):
    base = means(observed)
    pred = np.tile(base,(len(xt),1))
    for a in range(observed.shape[1]):
        mask = np.isfinite(observed[:,a])
        if not mask.any():
            continue
        z = x[mask]
        coef = np.linalg.solve(z@z.T + alpha*np.eye(mask.sum()), observed[mask,a]-base[a])
        pred[:,a] += (xt@z.T)@coef
    return pred


def corrected_utility(observed):
    mask = np.isfinite(observed)
    if not mask.any():
        raise ValueError('No labels for utility')
    base = means(observed)
    q = mask.mean()
    values = base + mask/q*(np.nan_to_num(observed)-base)
    return values, base


def direct_utility(x, observed, xt, reg):
    import torch
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    utility, base = corrected_utility(observed)
    anchor = int(base.argmax())
    advantage = torch.tensor(utility-utility[:,anchor,None],dtype=torch.float32)
    xx = torch.tensor(x,dtype=torch.float32); tt = torch.tensor(xt,dtype=torch.float32)
    offset = torch.tensor(base/.2,dtype=torch.float32)
    model = torch.nn.Linear(x.shape[1],observed.shape[1])
    torch.nn.init.zeros_(model.weight); torch.nn.init.zeros_(model.bias)
    optimizer = torch.optim.Adam(model.parameters(),lr=.02)
    initial = None
    for _ in range(300):
        optimizer.zero_grad()
        prob = (model(xx)+offset).softmax(1)
        loss = -(prob*advantage).sum(1).mean()+reg*sum(p.square().sum() for p in model.parameters())
        if initial is None:
            initial = float(loss.detach())
        loss.backward(); optimizer.step()
    with torch.no_grad():
        scores = (model(tt)+offset).softmax(1).numpy()
        train_scores = (model(xx)+offset).softmax(1).numpy()
    return scores, {'initial_objective':initial, 'last_preupdate_objective':float(loss.detach()),
                    'training_ht_routing_value':ht_score(observed,train_scores.argmax(1))/len(observed),
                    'parameter_squared_norm':float(sum(p.square().sum() for p in model.parameters()).detach())}


def fit(family,param,features,observed,agents):
    xs,ts = features['semantic']; xw,tw = features['text']
    if family == 'Global':
        scores = np.tile(means(observed),(len(ts),1))
    elif family == 'FactorRidge':
        scores = np.tile(factor_scores(observed,agents,param),(len(ts),1))
    elif family == 'SemanticRidge':
        scores = ridge_predict(xs,observed,ts,param)
    elif family == 'TextRidge':
        scores = ridge_predict(xw,observed,tw,param)
    elif family == 'DirectUtility':
        return direct_utility(xs,observed,ts,param)
    else:
        raise ValueError(family)
    return scores, {}


def feature_bank(embeddings,texts,groups,train,test):
    train = np.asarray(train); test = np.asarray(test)
    splits = inner_folds([groups[i] for i in train])
    def build(a,b):
        semantic = center_features(embeddings[a],embeddings[b])
        x,t,_ = text_features([texts[i] for i in a],[texts[i] for i in b])
        return {'semantic':semantic,'text':center_features(x,t)}
    bank = {'final':build(train,test),'inner':[]}
    for f in range(3):
        a,b = np.flatnonzero(splits!=f),np.flatnonzero(splits==f)
        assert not (set(groups[i] for i in train[a]) & set(groups[i] for i in train[b]))
        bank['inner'].append({'train':a,'val':b,'features':build(train[a],train[b]),
                             'train_groups':sorted(set(groups[i] for i in train[a])),
                             'val_groups':sorted(set(groups[i] for i in train[b]))})
    return bank


def route_case(bank,observed,agents,progress=lambda _:None):
    if np.isinf(observed).any() or not np.isin(observed[np.isfinite(observed)],[0,1]).all():
        raise ValueError('Observed gold must be binary or NaN')
    cv = {(f,p):0. for f in FAMILIES for p in PARAMS[f]}
    fold_trace = []
    for i,part in enumerate(bank['inner']):
        progress('inner_'+str(i))
        train,val = part['train'],part['val']
        for family,param in cv:
            scores,_ = fit(family,param,part['features'],observed[train],agents)
            cv[family,param] += ht_score(observed[val],scores.argmax(1))
        fold_trace.append({'train_groups':part['train_groups'],'validation_groups':part['val_groups'],
                           'train_labels':int(np.isfinite(observed[train]).sum()),
                           'validation_labels':int(np.isfinite(observed[val]).sum())})
    params = {f:max(PARAMS[f],key=lambda p:cv[f,p]) for f in FAMILIES}
    selected = max(FAMILIES,key=lambda f:cv[f,params[f]])
    actions,predictions,diagnostics = {},{},{}
    progress('final_fits')
    for family in FAMILIES:
        scores,diag = fit(family,params[family],bank['final'],observed,agents)
        if not np.isfinite(scores).all():
            raise ValueError('Nonfinite scores')
        actions[family] = scores.argmax(1).tolist()
        predictions[family] = scores.tolist()
        diagnostics[family] = diag
    actions['Selected'] = actions[selected].copy()
    return {'actions':actions,'scores':predictions,'trace':{'selected':selected,'params':params,
        'inner_scores':{f'{f}:{p}':v/len(observed) for (f,p),v in cv.items()},
        'inner_folds':fold_trace,'fit_diagnostics':diagnostics}}


def synthetic_smoke():
    x = np.linspace(-2,2,80)[:,None]
    y = np.column_stack([x[:,0]>0,x[:,0]<=0]).astype(float)
    p,d = direct_utility(x,y,x,.0001)
    p2,_ = direct_utility(x,y,x,.0001)
    assert np.array_equal(p,p2)
    accuracy = float(y[np.arange(len(x)),p.argmax(1)].mean())
    assert accuracy > .95
    assert d['last_preupdate_objective'] < d['initial_objective']
    p,_ = direct_utility(x,np.tile([1.,0.],(80,1)),x,.0001)
    assert (p.argmax(1)==0).all()
    return {'synthetic_rescue_accuracy':accuracy,'deterministic':True,'constant_control':True}
