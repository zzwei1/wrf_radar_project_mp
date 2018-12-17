# coding=utf-8

from builtins import filter
from builtins import map
import os
import sys

import dbf


def aggreate_dbf(dbf_list, headers, output_name, parent_dir=".", begin=0, end=-4):
    f = open(output_name, "w")
    f.write(",".join(headers) + "\n")
    for q in dbf_list:
        g = dbf.Table(os.path.join(parent_dir, q))
        g.open()
        l = q[begin:end] + "," + ",".join(map(str, list(g[0]))) + "\n"
        f.write(l)
    f.close()


def main():
    dirs = list(filter(os.path.isdir, sorted(os.listdir("."))))
    for d in dirs:
        files = os.listdir(d)    
        dbf_list = [p for p in files if p.endswith(".dbf")]
        f = dbf.Table(os.path.join(d, dbf_list[0]))
        f.open()
        headers = ['time'] + f.field_names
        f.close()
        aggreate_dbf(dbf_list, headers, "%s.csv" % d, parent_dir=d, begin=11, end=27)
        pass


if __name__ == "__main__":
    os.chdir(sys.argv[1])
    main()