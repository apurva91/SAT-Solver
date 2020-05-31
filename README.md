# SAT-Solver
## A very naive CDCL based SAT solver
### Assignment for CS508
---

### Task: 
- To design a SAT solver
- Run benchmarks on it to show solver's performance

In this implementation a CDCL based SAT solver is prepared. On the first look DPLL based SAT solver looks promising as it mostly does intutive part like purification and unit propgation, it works good for random test cases, but for industrial purposes CDCL is used mainly due to these three reasons.
- The variable is chosen randomly
- Chronologically all branches are checked out
- No learning from the current partial assignment, throws it all away.

CDCL takes care of these three things, but for variable selection we use the below heuristics:
- **Random**: The way it is already done.
- **Ordered**: The first variable that is unassigned in the order 1,2,3... is chosen.
- **Dynamic Largest Individual Sum (DLIS)**: The literal that occurs more frequently. By doing this we will be able to resolve maximum number of clauses at once.
- **Largest Variable Sum (LVS)**: The variable that occurs more frequently is chosen. The count is computed once in the beginning and it is static, unlike DLIS does it everytime.
- **Jeroslow–Wang (JW)**: Similar to DLIS but more weight is given to a literal in shorter clause compared to a longer clause weight is given by 2^-length.


### Usage:
```
pip3 install -r requirements.txt
```
#### in Terminal
```
python3 sat_solver.py test_cases/unsat.cnf --strategy=DLIS
```
#### In Jupyter Notebook
Refer to the last of Jupyter Notebook if you wish to run it from there.

### Benchmarking Results

|Strategy|||||Random|||Ordered|||LVS|||JW|||DLIS|||
|--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |--- |
|File|Variables|Clauses|SAT|Read Time|Time|Branches|Implications|Time|Branches|Implications|Time|Branches|Implications|Time|Branches|Implications|Time|Branches|Implications|
|test_cases/19x19queens.cnf|361|10735|True|0.0375969|0.7245011329650879|22|408|13.811938762664795|210|3863|20++|271|5765|20++|473|1964|20++|464|1722|
|test_cases/flat30-13.cnf|90|300|True|0.00499797|0.07964015007019043|15|174|0.05555391311645508|14|164|0.026264667510986328|11|79|0.042482614517211914|24|98|0.03744649887084961|24|98|
|test_cases/flat50-102.cnf|150|545|True|0.00365877|0.0988621711730957|18|461|0.1361086368560791|54|494|0.07672238349914551|18|463|0.07051301002502441|23|196|0.07769441604614258|23|196|
|test_cases/uf20-01000.cnf|20|91|True|0.00158358|0.03455471992492676|26|218|0.023804187774658203|10|124|0.010464191436767578|6|55|0.013496637344360352|4|29|0.008116960525512695|4|29|
|test_cases/uf50-0101.cnf|50|218|True|0.00287247|0.580223798751831|182|2515|0.11874794960021973|49|769|0.027406692504882812|17|170|0.045702457427978516|24|228|0.05267167091369629|24|228|
|test_cases/unsat.cnf|2|4|False|0.00106788|0.0002651214599609375|1|5|0.0002639293670654297|1|5|0.0003077983856201172|1|5|0.0002994537353515625|1|5|0.00031113624572753906|1|5|
|test_cases/unsat1.cnf|3|8|False|0.000771999|0.0007119178771972656|3|11|0.0006284713745117188|3|11|0.000370025634765625|3|11|0.0009434223175048828|3|11|0.0005941390991210938|3|11|
|test_cases/uuf50-0100.cnf|50|218|False|0.00169492|0.9695279598236084|242|3920|0.2140347957611084|73|1003|0.08237147331237793|26|496|0.15317153930664062|47|738|0.17574501037597656|47|738|
|test_cases/bmc-2.cnf|2810|11683|True|0.0687082|19.129653215408325|160|4943|65.78856468200684|632|12267|49.41663098335266|333|14387|32.43623399734497|246|7237|29.926966428756714|220|7939|
|test_cases/uf100-016.cnf|100|430|True|0.00383091|20++|1263|26013|16.33281707763672|1248|30633|1.648735761642456|202|5578|3.3911619186401367|372|7052|3.6570186614990234|372|7052|
|test_cases/uf125-04.cnf|125|538|True|0.00412393|13.79047155380249|952|20115|20++|1118|31940|20++|985|30505|20++|997|24494|20++|1131|28430|
|test_cases/uf150-02.cnf|150|645|True|0.00486898|20++|1040|24398|20++|764|22486|17.072136163711548|710|25354|20++|924|24552|20++|958|25294|
|test_cases/uf75-02.cnf|75|325|True|0.00294042|0.04744672775268555|22|161|1.6036314964294434|254|5623|1.289762258529663|175|3687|0.09412932395935059|25|115|0.14099764823913574|25|115|
|test_cases/uuf75-04.cnf|75|325|False|0.00568295|14.430735349655151|1303|22320|2.0134904384613037|314|6849|1.1951148509979248|179|4213|1.4544122219085693|243|4574|1.3848938941955566|243|4574|
|test_cases/uf100-0167.cnf|100|430|True|0.0128238|13.863039255142212|1133|25042|50.43213486671448|2159|65072|0.2616395950317383|45|898|0.18059206008911133|52|419|0.1850593090057373|52|419|
|test_cases/bmc-7.cnf|8710|39774|True|0.312685|300++|7519|202699|300++|7946|134561|280.04323983192444|651|29087|300++|6987|159982|300++|6427|126504|


The testcases are downloaded from EduSAT and SATLIB.