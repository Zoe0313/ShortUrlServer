[Redis-Stack-Bitnami-Helm-Chart](https://github.com/kamalkraj/Redis-Stack-Bitnami-Helm-Chart)

Deploy redis-stack-server by helm
```
git clone https://github.com/kamalkraj/Redis-Stack-Bitnami-Helm-Chart.git
cd Redis-Stack-Bitnami-Helm-Chart/
helm install redis-stack-server . -n vsanperf-shorturl  --debug
```

After installing, we got below infomations:
```
NOTES:
CHART NAME: redis
CHART VERSION: 17.11.7
APP VERSION: 7.0.11

** Please be patient while the chart is being deployed **

Redis&reg; can be accessed on the following DNS names from within your cluster:

    redis-stack-server-master.vsanperf-shorturl.svc.cluster.local for read/write operations (port 6379)
    redis-stack-server-replicas.vsanperf-shorturl.svc.cluster.local for read-only operations (port 6379)

To get your password run:

    export REDIS_PASSWORD=$(kubectl get secret --namespace vsanperf-shorturl redis-stack-server -o jsonpath="{.data.redis-password}" | base64 -d)

    G76B7zt4C9

To connect to your Redis&reg; server:

1. Run a Redis&reg; pod that you can use as a client:

   kubectl run --namespace vsanperf-shorturl redis-client --restart='Never'  --env REDIS_PASSWORD=$REDIS_PASSWORD  --image docker.io/redis/redis-stack-server:6.2.6-v7 --command -- sleep infinity

   Use the following command to attach to the pod:

   kubectl exec --tty -i redis-client --namespace vsanperf-shorturl -- bash

2. Connect using the Redis&reg; CLI:
   REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h redis-stack-server-master
   REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h redis-stack-server-replicas

To connect to your database from outside the cluster execute the following commands:

    kubectl port-forward --namespace vsanperf-shorturl svc/redis-stack-server-master 6379:6379 &
    REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h 127.0.0.1 -p 6379
```

We can connect to redis db by attaching redis-client pod:
```
$ kubectl exec --tty -i redis-client --namespace vsanperf-shorturl -- bash
```

Firstly, we create user "shorturl" and set password "shorturl" to it:
```
root@redis-client:/# redis-cli -h redis-stack-server-master
redis-stack-server-master:6379> auth G76B7zt4C9
OK
redis-stack-server-master:6379> acl list
1) "user default on #38fe51133b34e6ef08e83fc3ab13e197603fbe44832ab3633b2eff25aed88a0f ~* &* +@all"
redis-stack-server-master:6379> acl setuser shorturl on  ~* &* +@all
OK
redis-stack-server-master:6379> acl setuser shorturl >shorturl
OK
redis-stack-server-master:6379>  acl getuser shorturl
 1) "flags"
 2) 1) "on"
    2) "allkeys"
    3) "allchannels"
    4) "allcommands"
 3) "passwords"
 4) 1) "aa59d99893b035c23b88b313d7e0af40e62391cbc36c9f5bbbaa2bc2686da9c1"
 5) "commands"
 6) "+@all"
 7) "keys"
 8) 1) "*"
 9) "channels"
10) 1) "*"
redis-stack-server-master:6379> acl list
1) "user default on #38fe51133b34e6ef08e83fc3ab13e197603fbe44832ab3633b2eff25aed88a0f ~* &* +@all"
2) "user shorturl on #aa59d99893b035c23b88b313d7e0af40e62391cbc36c9f5bbbaa2bc2686da9c1 ~* &* +@all"
redis-stack-server-master:6379> save
OK
```

Then, we can connect to db by shorturl.
Generating short key on Web https://vsanvia.broadcom.net/shorten and check the keys count:
```
root@redis-client:/# redis-cli -u redis://shorturl:shorturl@redis-stack-server-master.vsanperf-shorturl.svc.cluster.local:6379
redis-stack-server-master.vsanperf-shorturl.svc.cluster.local:6379> dbsize
(integer) 2
redis-stack-server-master.vsanperf-shorturl.svc.cluster.local:6379> dbsize
(integer) 3
redis-stack-server-master.vsanperf-shorturl.svc.cluster.local:6379> keys *
1) ":src.schema.Url:index:hash"
2) ":src.schema.Url:01J8YG0NP65G5F8R6FDW8BNK2C"
3) ":src.schema.Url:01J8YGF5TVD7ZBVKYQF8NSEV42"
```

Delete redis-stack-server by helm:
```
helm uninstall redis-stack-server . -n vsanperf-shorturl
```
