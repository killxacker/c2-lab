## Purple Team stsenariylari

### 1. Beaconing detektsiyasi (T1071.001, T1027)
1. C2 + beacon ishga tushiring (--sleep 5)
2. Suricata/Zeek loglarida /checkin patternini kuzating
3. rules/c2_beacon_http.yml ni test qiling

### 2. Discovery emulyatsiyasi + Sigma
c2> use <bid>
c2(<bid>)> shell whoami -a T1087
c2(<bid>)> shell tasklist -a T1057
c2(<bid>)> shell systeminfo -a T1082
Sysmon EID 1 loglari bilan rules/c2_suspicious_cmd.yml ni solishtiring.

### 3. Exfiltration (T1005)
c2(<bid>)> download /etc/passwd
# C2'da loot/<bid>/ ga tushadi, files komandasi bilan ko'ring

### 4. Tool transfer (T1105)
c2(<bid>)> upload /tmp/tool.sh

### 5. Coverage hisoboti
c2> coverage
