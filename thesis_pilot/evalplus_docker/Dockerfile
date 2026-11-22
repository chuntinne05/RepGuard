FROM python:3.11-slim
RUN pip install --no-cache-dir numpy==2.1.3 tqdm==4.67.1 termcolor==2.5.0 fire==0.7.0 appdirs==1.4.4 \
    wget==3.2 tempdir==0.7.1 multipledispatch==1.0.0 psutil==6.1.1 rich==13.9.4 tree_sitter==0.23.2 \
    tree-sitter-python==0.23.6 datasets==3.2.0
COPY evalplus /opt/evalplus_src/evalplus
COPY runner.py /opt/runner.py
ENV PYTHONPATH=/opt/evalplus_src
ENTRYPOINT ["python", "/opt/runner.py"]
