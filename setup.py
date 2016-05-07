#!/usr/bin/env python

from distutils.core import setup

setup(
    name="mediawiki-tools",
    version="0.99",
    description="Various tools for Mediawiki sites",
    author="Sebastian Rittau",
    author_email="srittau@rittau.org",
    packages=["mwtools"],
    scripts=["bin/mw-template-argument-count"],
    data_files=[("", ["LICENSE"])],
)
