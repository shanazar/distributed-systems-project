FROM jupyter/datascience-notebook:x86_64-ubuntu-22.04

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir dask