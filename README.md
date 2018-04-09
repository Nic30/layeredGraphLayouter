# layeredGraphLayouter - !This repository will be removed and elk wrapper will be used instead because ELK is big and evolving software!

[![Travis-ci Build Status](https://travis-ci.org/Nic30/layeredGraphLayouter.png?branch=master)](https://travis-ci.org/Nic30/layeredGraphLayouter)[![PyPI version](https://badge.fury.io/py/layeredGraphLayouter.svg)](http://badge.fury.io/py/layeredGraphLayouter)[![Coverage Status](https://coveralls.io/repos/github/Nic30/layeredGraphLayouter/badge.svg?branch=master)](https://coveralls.io/github/Nic30/layeredGraphLayouter?branch=master)[![Documentation Status](https://readthedocs.org/projects/layeredGraphLayouter/badge/?version=latest)](http://layeredGraphLayouter.readthedocs.io/en/latest/?badge=latest)

layeredGraphLayouter is python package for automatic generating of layered graphs used in dataflow/electronic/process/HDL visualization.

This was originally unofficial port of ELK (Eclipse Layout Kernel https://www.eclipse.org/elk/ https://github.com/eclipse/elk, http://www.rtsys.informatik.uni-kiel.de/en/research/kieler).
but I was forced to do some radical optimizations which means this library is ELK-like more than ELK port.

This library currently has 3 exporters:

* toMxGraph - creates MxGraph xml which can be opened for example at draw.io
* toJson - simple json format
* toSvg - SVG image
