BenFuzz settings:
- cmap -> fuzzFactor 100
- maxp -> fuzzFactor 2
- loca -> fuzzFactor 5
- glyf -> fuzzFactor 80


Performances:
- native: range(10, 100, 10) -> ~12/13s per font on win7 2gb ram
- native ben: range(10, 70, 10) -> ~1.5s per font on win7 2gb ram (considering fonts not rendered)