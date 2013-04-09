#!/usr/bin/env python
from optparse import OptionParser, OptionGroup
import os
import sys
import re
import datetime
import logging
import glob


HOME = os.path.expanduser('~')
pythonlibpath = HOME

" A1,B1,C1,D1,E1,F1,G1,I3,C2,B2,F2,E2,A2,D2,G2"
type_to_name = dict(
    A1="sword",
    B1="sling",
    C1="arch",
    D1="hops",
    E1="horse",
    F1="char",
    G1="cat",
    I3="Cerberus",
    G3="Centaur",
    E3="Minotaur",
    C3="Harpy",
    D3="Medusa",
    H3="Pegasus",
    C2="LS",
    B2="BIR",
    F2="TRI",
    E2="FAST",
    A2="SLOW",
    D2="FIRE",
    G2="CS",
    A4="militia",
    M3="Envoy",
    F3="Manticore",
    B3="Hydra",
)


class Stat(object):
    
    def __init__(self, stats, defeated, attacker, types, nums):
        self.stats = stats
        self.defeated = defeated
        self.attacker = attacker
        self.types = types
        self.nums = nums
        assert(len(types) == len(nums))

    def name(self, t):
        n = type_to_name.get(t, None)
        if not n:
            n = "unk " + t
        return n

    def stat(self, t):
        try:
            c = self.types.index(t)
            return self.nums[c]
        except ValueError:
            return 0

    @property
    def attack(self):
        return "Killed" if self.defeated else "Lost"

    @property
    def defense(self):
        return "as Attacker" if self.attacker else "as Defender"

    def __repr__(self):
        l = "Stat(%s %s [%d])" % (self.attack, self.defense, self.stats)
        
        names = map(lambda t: self.name(t), self.types)
        res = []
        for cnt, name in enumerate(names):
            res.append("%s=%d" % (name, self.nums[cnt]))
             
        l += "\n\t" + ", ".join(res) 
        return l 

def parse(wall):
    exp_types = re.compile(r".*&list=(.*)\[/img\]")
    exp_section = re.compile(r"\[size=\d+\](.*)\[/size\]")
    exp_stats = re.compile(r".* \((\d+)\)")
    lines = file(wall, "r").readlines()
    defeated = False
    attacker = False
    types = []
    nums = []
    stats = 0
    allstats = []
    for l in lines:
        l = l.strip()
        reg = exp_types.match(l)
        if reg:
            types += reg.group(1).split(".")
            continue
        reg = exp_section.match(l)
        if reg:
            section = reg.group(1)
            if "?" in section:
                thisnums = section.split("?")
                thisnums = filter(lambda x: x, thisnums)
                thisnums = map(lambda x: int(x), thisnums)
                nums += thisnums
            elif "[/color]" in section:
                section = section.replace("[/color]", "").replace("[color=#fff]", "")
                thisnums = section.split(".")
                thisnums = filter(lambda x: x, thisnums)
                thisnums = map(lambda x: int(x), thisnums)
                nums += thisnums
            else:
                if "defeated" in section.lower():
                    if types:
                        s = Stat(stats, defeated, attacker, types, nums)
                        allstats.append(s)
                        types = []
                        nums = []
                    defeated = True
                    continue  
                elif "losses" in section.lower():
                    if types:
                        s = Stat(stats, defeated, attacker, types, nums)
                        allstats.append(s)
                        types = []
                        nums = []
                    defeated = False
                    continue
                elif "attacker" in section.lower():
                    if types:
                        s = Stat(stats, defeated, attacker, types, nums)
                        allstats.append(s)
                        types = []
                        nums = []
                    attacker = True
                elif "defender" in section.lower():
                    if types:
                        s = Stat(stats, defeated, attacker, types, nums)
                        allstats.append(s)
                        types = []
                        nums = []
                    attacker = False
                else:
                    raise Exception("Parse error %s" % l)
                stats = int(exp_stats.match(section).group(1))

    if types:
        s = Stat(stats, defeated, attacker, types, nums)
        allstats.append(s)

    return allstats


def compare_walls(oldpath, newpath):
    oldstats = parse(oldpath)
    newstats = parse(newpath)
    changed = False
    
    for (defeated, attacker) in ((1, 1), (1, 0), (0, 1), (0, 0)):
        olds = filter(lambda x: x.defeated == defeated and x.attacker == attacker, oldstats)[0]
        news = filter(lambda x: x.defeated == defeated and x.attacker == attacker, newstats)[0]
        types = []
        nums = []
        stats = 0
        for t in news.types:
            oldstat = olds.stat(t)
            newstat = news.stat(t)
            if oldstat == newstat:
                continue
            types.append(t)
            nums.append(newstat - oldstat)
            stats += newstat - oldstat
        
        if types:
            s = Stat(stats, defeated, attacker, types, nums)
            print s
            changed = True
    
    return changed


def compare_swap_new_wall(options):
    grepolis = os.path.join(pythonlibpath, "grepolis")
    oldpath = os.path.join(grepolis, "wall.txt")
    newpath = os.path.join(grepolis, "newwall.txt")

    if compare_walls(oldpath, newpath):
        d = str(datetime.datetime.now().isoformat()).replace(":", "_")
        open(os.path.join(grepolis, "wall_%s.txt" % d), "w").write(file(oldpath, "r").read())
        open(oldpath, "w").write(file(newpath, "r").read())
    else:
        logging.info("No Change")


def compare_back_history_wall(options):
    grepolis = os.path.join(pythonlibpath, "grepolis")
    logging.info("Looking into %s", grepolis)
    
    walls = glob.glob(os.path.join(grepolis, "wall*.txt"))
    walls = map(lambda x: (os.path.getmtime(x) if os.path.basename(x) != "wall.txt" else sys.maxint, x), walls)
    walls.sort()
    assert(os.path.basename(walls[-1][1]) == "wall.txt")
    
    for cnt, w in enumerate(walls[:-1]):
        print "*" * 80
        neww = walls[cnt + 1]
        print os.path.basename(w[1]), os.path.basename(neww[1])
        compare_walls(w[1], neww[1])
        print "*" * 80


def main():
    parser = OptionParser(usage="%prog [options]", version="%prog 1.0")
    
    group = OptionGroup(parser,  "Display Options", "Verbose...")
    group.add_option("-b", "--back", help="Print back history",
                     default=False, action="store_true", dest="back")
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    if args:
        parser.error("Too many arguments")
    
    logging.basicConfig(level=logging.INFO,
                         format='%(asctime)s.%(msecs)03d %(levelname)-8s: %(message)s',
                         datefmt='%Y-%m-%d %H:%M:%S',
                         stream=sys.stdout)
    logging.info("This script uses http://grepolis.potusek.eu/")
    
    if options.back:
        compare_back_history_wall(options)
    else:
        compare_swap_new_wall(options)        
    

if __name__ == '__main__':
    sys.exit(main())
