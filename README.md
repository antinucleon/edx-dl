# edx-dl

## 0. Motivation

I was using `https://github.com/coursera-dl/edx-dl` to backup some courses I want to learn but delayed due to 1000+ reasons. However seems this project is no longer maintained. So I spend a few hours to write a small tool.

This script is usable but I don't have time to do more test, and I have no plan to maintain this project. However it is straightforward to update because it is just 200 lines of code.

## 1. Usage
- Download `chromedriver` and put it into `./bin`
- Install aria2
- Run `pip install -r requirements.txt`
- Run `edx-dl.py`, input user name, password, and course url (eg: `https://learning.edx.org/course/course-v1:CaltechX+BEM1105x+3T2020/home`)
- Wait for a while

## 2. Remark
- Headless mode may be buggy due to lacking wait for some loadings. However I am lazy to make it correct. 
