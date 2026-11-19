## Slide 01


Agenda

Progress since the October report

Four studies, a working verification layer, and a plan for the next experiments.

1

Work completed

What we ran, what we built, and how we moved

beyond checking only the final answer.

2

What we learned

What the results tell us about review, task

completion and the way answers are judged.

3

Research direction

How we plan to test whether verification

feedback helps agents correct their work.

4

Next steps

What Tín and Trung will prepare before the

next comparison.

The main question is how agents can check and pass on analytical work more reliably.


---


## Slide 02


What we have done since the last report

1,265

new responses across four studies

720

Evidence checking

120 pairs · 24 groups

288

Financial report QA

24 questions · 2 prompts

113

Data workspaces

6 tasks · 36 runs

144

SQL with specified

interpretations

12 tasks · 24 cases

We started with evidence checking and report questions, then moved to agents working with files and

databases. This gave us examples of both reasoning errors and failures to finish a task.

Alongside these runs, we built a checker that links each SQL query to its source data and the requirements it is

meant to satisfy.


---


## Slide 03


Does using a different reviewer help?

We compared asking a model to check its own answer with asking the other model to review it.

Both studies found an average gain of about 2 percentage points, but the confidence intervals include zero. We

do not yet have clear evidence that switching models improves review.

These results are why we have kept reputation learning on hold.

Chart: cross-model minus self-review, +2.08 pp in both studies; 95% CIs [−0.42, +4.59] and [−4.17, +8.33].


---


## Slide 04


What happened when agents worked with real files

We connected the agents to CSV, JSON, SQLite and PDF files, then examined 36 runs across six tasks.

9

14

13

Matched the reference

The submitted table matched the

expected rows and columns.

Returned a different table

These outputs needed closer

review: the issue could be the

chosen field, interpretation or table

shape.

No final table

The agent stopped without a final

table, often after spending its

budget searching or generating

output.

The key distinction is between failing to finish and finishing with a result that needs checking. We use the

traces to understand which problem occurred before deciding how another agent could help.


---


## Slide 05


Three cases we looked at more closely

1

Wrong attribute

2

Unclear meaning

3

Extra output column

Fund manager nationality

Person name / fund name

Nationality + correct join

We asked for nationality. The

query used names as a proxy, even

though a Nationality field was

available in the source.

“Fund abbreviation”

SecuAbbr

or

ChiNameAbbr

The source had two plausible

abbreviation columns. We need to

settle the intended meaning before

deciding which answer is correct.

Correct names; extra ID

Procedure name

ID

The names and their order were

correct, but an extra ID column

caused a mismatch with the

expected table.

These cases call for different fixes, rather than a single “wrong answer” category.


---


## Slide 06


Building checks into the handoff

We have implemented a checker for SQL queries. It compares the query with the source schema and

system-defined requirements, then reports what is satisfied, violated or unresolved.

The review loop we will test next

SQL agent

Writes a query

Checker

Checks source use

Reviewer

Reads the findings

Re-execution

Runs the revised SQL

Met

Violated

Unresolved

29

New tests

87

Tests passed in the scoped suite

20/20

SQL outputs reproduced

byte for byte

The tests cover source binding and handoff consistency. Replaying old SQL reproduced the same output bytes; the

next experiment will test whether the checker helps agents correct their work.


---


## Slide 07


Preparing a broader SQL evaluation

We prepared 204 SpecBridge tasks across 12 databases and split them by database, so we can develop on one

group before evaluating on the others.

45

67

92

45 for development

Used in the current pilot

67 for validation

For the next comparison

92 set aside

Kept for final evaluation

90/90

Reference queries matched as expected

We also tested wrong interpretations and missing or extra rows. These checks confirmed that

the grader rejected the cases it should reject.

One task changed score between SQLite versions, so we fixed the execution engine before running the models. The

next technical step is to extend the checker to more complex SQL.


---


## Slide 08


Self-review did better in the SQL pilot

We tested Qwen (A) and Gemma (B) on 12 SQL tasks, each with two requested interpretations. The six

workflows produced 144 responses in total.

Both self-review workflows solved 21 of 24 cases. Cross-model review solved 19 and 20, which was 6.25

percentage points lower on average in this pilot.

We will now test whether specific verification feedback changes this result.

Chart: A18/24, B19/24, AA21/24, BB21/24, AB19/24, BA20/24.


---


## Slide 09


Where we take the research next

Can verification feedback help agents repair an analysis

more reliably than asking them to check it again?

What we can already study

We have real traces showing wrong fields,

ambiguous requests and incomplete outputs.

The checker records why a query meets or breaks

a requirement, and what still needs review.

What we need to compare

1.

Review without diagnostic feedback.

2.

Review with the checker’s findings.

3.

Review with shuffled findings.

We will keep the tools and review budget the same, then repeat the comparison on new databases. We will measure

correct completion, repairs, new errors and total cost.


---


## Slide 10


Next steps for Tín and Trung

We will first agree on what counts as a correct result, then run the next comparison with a fixed protocol.

Tín

Trung

1.

Extend the checker to handle CTEs and more

complex queries.

2.

Run strong single-model, self-review and

cross-model baselines with the same tools.

3.

Keep a reproducible record of outputs, token

use and running time.

1.

Review the source data and resolve ambiguous

cases using a shared rubric.

2.

Check the proposed contribution against the

closest research papers.

3.

Find analysts or students who can try a real

reporting workflow.

Deliverable: checker coverage

and baseline results

Deliverable: reviewed cases

and a pilot workflow

Together: review cases, freeze the protocol, then test on the databases set aside.


---
