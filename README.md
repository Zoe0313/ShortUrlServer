# vSAN URL shortener

## Description
With the transition to Broadcom, we lost access to the via.vmw.com short URL service. 
This has created a need for a new URL-shortening service that can be internally deployed and managed. 
To address this, we propose the development of a new short URL application, which will be deployed on our dogfooding environment.

## Installation

[Install Redis on MacOS](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-mac-os/)

[Install Redis on CentOS](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-centos-8)

[Run Redis Stack on Docker](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/docker/)

[Query data in Redis](https://redis.io/docs/latest/develop/interact/search-and-query/query/)

## Dev Env

- Clone the repository from Gitlab
```
$ git clone git@gitlab.eng.vmware.com:vsanslackbot/url-shortener.git url_shortener
$ cd url_shortener
```

- Create a Python virtual environment, and install the project dependencies
```
$ python3.11 -m venv venv
$ . ./venv/bin/activate
$ pip3 install -r requirements.txt
```

- Get a Redis Stack database up and running
```
$ docker login vsaninternaltools-docker-local.artifactory.eng.vmware.com
lzoe
cmVmdGtuOjAxOjE3NTQzODE0NjQ6YzJqcUlaOWUwamVJRmNhSXo3eDIwS20zSWpT
$ docker pull vsaninternaltools-docker-local.artifactory.eng.vmware.com/stage/slackbot/redis-stack:latest
$ docker tag vsaninternaltools-docker-local.artifactory.eng.vmware.com/stage/slackbot/redis-stack:latest redis/redis-stack:latest
$ docker run -d -p 6379:6379 -p 8001:8001 redis/redis-stack
$ docker exec -it <redis-container-name> /bin/bash
# redis-cli --version
redis-cli 7.4.0
```

- Start a Redis Stack by args
```
$ mkdir /local-data
$ docker run -d \
  -v /local-data/:/data \
  -p 10001:6379 \
  -p 13333:8001 \
  -e REDIS_ARGS="--requirepass shorturl --save 60 1000 --appendonly yes" \
  -e REDISTIMESERIES_ARGS="RETENTION_POLICY=20" \
  --name redis \
  --restart always \
  redis/redis-stack:latest
$ export REDIS_OM_URL=redis://<username>:<password>@<host>:<port> 
  (on production we use export REDIS_OM_URL=redis://:shorturl@localhost:10001)
```

Descriptions:
`--save 60 1000` -  this configuration will make Redis automatically dump the dataset to disk 
                    every 60 seconds if at least 1000 keys changed
`--appendonly yes` -  The append-only file is an alternative, fully-durable strategy for Redis.
                      It became available in version 1.1.

Check ls -ld /local-data/ on host machine to view the directory permissions.
```
[root@w3-vsan-sherpa-10-208-103-200 ~]# ls -ld /local-data/
drwxr-xr-x. 3 root root 43 Jul 31 01:08 /local-data/
```

- Start the Flask application in development mode
```
$ export REDIS_OM_URL=redis://default:@localhost:6379
$ export SHORT_KEY_PREFIX=http://127.0.0.1:5000/
$ export FLASK_ENV=development
$ flask run
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Start the Flask application as a background process
```
$ nohup flask run
```

Start the Flask application with HTTP on Production
```
$ export REDIS_OM_URL=redis://:shorturl@localhost:10001
$ export SHORT_KEY_PREFIX=http://vsanvia.vmware.com/
$ unset FLASK_ENV
$ nohup flask run --host 0.0.0.0 --port 80 > /var/log/shorturl.log 2>&1 &
```

Start the Flask application with HTTPS
```
Generate a self-signed Ssl cetificate and private key:
$ mkdir ~/certs
$ openssl req -newkey rsa:2048 -nodes -keyout ~/certs/selfsigned.key -x509 -days 365 -out ~/certs/selfsigned.crt
$ nohup flask run --host 0.0.0.0 --port 443 --cert /root/certs/selfsigned.crt --key /root/certs/selfsigned.key > /var/log/shorturl.log 2>&1 &
```
But the cert is no use on production. Query https://vsanvia.vmware.com/api/ to generate short url or redirect to long url, the ssl cetificate warning always occur.

- Test short url generator functionality
```
$ python test.py
Got short url: http://127.0.0.1:5000/cc3ZY
url details: {'alias_short_url': '', 'create_at': 'Fri, 19 Jul 2024 00:00:00 GMT', 'expire_time': 'Thu, 18 Jul 2024 00:00:00 GMT', 'original_url': 'https://bugzilla.eng.vmware.com/report.cgi?format=table&action=wrap&x_axis_field=component&y_axis_field=&z_axis_field=&query_format=report-table&ctype=&short_desc_type=allwordssubstr&short_desc=&longdesc_type=allwordssubstr&longdesc=&keywords_type=nowords&keywords=&target_milestone_type=allwords&target_milestone=&product=ESX&bug_status=new&bug_status=assigned&bug_status=reopened&priority=---&priority=P0&priority=P1&priority=P2&cf_build_type=equals&cf_build=&cf_branch_type=anywordssubstr&cf_branch=&cf_build_types_type=anywordssubstr&cf_build_types=&cf_build_target_type=anywordssubstr&cf_build_target=&cf_change_type=anywordssubstr&cf_change=&cf_test_id_type=equals&cf_test_id=&emailtype1=exact&email1=&emailtype2=exact&email2=&cf_type=Defect&cf_failed_type=equals&cf_failed=&cf_attempted_type=equals&cf_attempted=&cf_eta_type=&cf_doc_impact_type=equals&cf_i18n_impact_type=equals&host_op_sys_type=anyexact&guest_op_sys_type=anyexact&cf_jira_sync_type=equals&cf_rank_type=&cf_gss_rank_type=&cf_overall_update_type=anywordssubstr&cf_overall_update=&cf_rcca_req_type=equals&cf_rcca_done_type=equals&cf_rcca_sign_off_type=equals&cf_no_req_details_type=anywordssubstr&cf_no_req_details=&cf_feature_details_type=anywordssubstr&cf_feature_details=&cf_documentation_details_type=anywordssubstr&cf_documentation_details=&cf_other_details_type=anywordssubstr&cf_other_details=&cf_security_type=equals&cf_cwe_type=&cf_viss_type=&changedin=&chfieldfrom=&chfieldto=Now&chfieldoldvalue=&changes_from_product_name=0&changes_from_version_name=&chfieldvalue=&changes_to_product_name=0&changes_to_version_name=&bugidtype=include&bug_id=&votes=&sr_type=equals&sr=&sr_count_type=equals&sr_count=&cases_type=equals&cases=&case_count_type=equals&case_count=&wolken_cases_type=equals&wolken_cases=&wolken_case_count_type=equals&wolken_case_count=&jira_sds_type=equals&jira_sds=&jira_sd_count_type=equals&jira_sd_count=&kb_type=equals&kb=&kb_count_type=equals&kb_count=&field0-0-0=fix_by_version_name&type0-0-0=equals&value0-0-0=main&field0-1-0=category&type0-1-0=equals&value0-1-0=VSAN&field0-1-1=product&type0-1-1=equals&value0-1-1=VSAN&field0-1-2=category&type0-1-2=equals&value0-1-2=vSAN+File+Services&field0-1-3=category&type0-1-3=equals&value0-1-3=VDFS&field0-2-0=component&type0-2-0=notequals&value0-2-0=SnapService&field0-3-0=component&type0-3-0=notequals&value0-3-0=Automation&field0-4-0=component&type0-4-0=notequals&value0-4-0=SnapService+Appliance&field0-5-0=component&type0-5-0=notequals&value0-5-0=Tracing&field0-6-0=component&type0-6-0=notequals&value0-6-0=Active+Directory&field0-7-0=component&type0-7-0=nowords&value0-7-0=Documentation%2CBuild&field0-8-0=cf_type&type0-8-0=notequals&value0-8-0=Documentation&field0-9-0=cf_type&type0-9-0=notequals&value0-9-0=Task&field0-10-0=component&type0-10-0=notequals&value0-10-0=Tests&field0-11-0=component&type0-11-0=notequals&value0-11-0=SKY&field0-12-0=component&type0-12-0=notequals&value0-12-0=SnapService&field0-13-0=component&type0-13-0=notequals&value0-13-0=Humbug&field0-14-0=component&type0-14-0=notequals&value0-14-0=zeta&field1-0-0=keywords&type1-0-0=nowordssubstr&value1-0-0=vsan-90u1-release&field1-1-0=fix_by_version_name&type1-1-0=notequals&value1-1-0=Future&cmdtype=doit&columnlist=creation_ts%2Cdelta_ts%2Cpriority%2Cbug_status%2Cresolution%2Cassigned_to%2Creporter%2Ccomponent%2Ckeywords%2Cfix_by%2Ccf_eta%2Cshort_desc&backButton=true&textSaver=chfieldto%3DNow%7Cvalue0-0-0%3Dmain%7Cvalue0-1-0%3DVSAN%7Cvalue0-1-1%3DVSAN%7Cvalue0-1-2%3DvSAN%2520File%2520Services%7Cvalue0-1-3%3DVDFS%7Cvalue0-2-0%3DSnapService%7Cvalue0-3-0%3DAutomation%7Cvalue0-4-0%3DSnapService%2520Appliance%7Cvalue0-5-0%3DTracing%7Cvalue0-6-0%3DActive%2520Directory%7Cvalue0-7-0%3DDocumentation%252CBuild%7Cvalue0-8-0%3DDocumentation%7Cvalue0-9-0%3DTask%7Cvalue0-10-0%3DTests%7Cvalue0-11-0%3DSKY%7Cvalue0-12-0%3DSnapService%7Cvalue0-13-0%3DHumbug%7Cvalue0-14-0%3Dzeta%7Cvalue1-0-0%3Dvsan-90u1-release%7Cvalue1-1-0%3DFuture%7C&checkboxSaver=sPeople%3D000000000000000000000000%7CsBooleanSearch%3D00%7C&keywords=vsan-svs&keywords=vsan-svs-get-well&keywords=vsan-90u1-release&keywords=testissues&keywords=vsan-esa-dedup&keywords=vsan-90-opportunistic', 'pk': '01J34QN2VYKGNQYJ8JAZRHZ1ZZ', 'short_url': 'http://127.0.0.1:5000/cc3ZY', 'user_id': None}
redirect to: https://bugzilla.eng.vmware.com/report.cgi?format=table&action=wrap&x_axis_field=component&y_axis_field=&z_axis_field=&query_format=report-table&ctype=&short_desc_type=allwordssubstr&short_desc=&longdesc_type=allwordssubstr&longdesc=&keywords_type=nowords&keywords=&target_milestone_type=allwords&target_milestone=&product=ESX&bug_status=new&bug_status=assigned&bug_status=reopened&priority=---&priority=P0&priority=P1&priority=P2&cf_build_type=equals&cf_build=&cf_branch_type=anywordssubstr&cf_branch=&cf_build_types_type=anywordssubstr&cf_build_types=&cf_build_target_type=anywordssubstr&cf_build_target=&cf_change_type=anywordssubstr&cf_change=&cf_test_id_type=equals&cf_test_id=&emailtype1=exact&email1=&emailtype2=exact&email2=&cf_type=Defect&cf_failed_type=equals&cf_failed=&cf_attempted_type=equals&cf_attempted=&cf_eta_type=&cf_doc_impact_type=equals&cf_i18n_impact_type=equals&host_op_sys_type=anyexact&guest_op_sys_type=anyexact&cf_jira_sync_type=equals&cf_rank_type=&cf_gss_rank_type=&cf_overall_update_type=anywordssubstr&cf_overall_update=&cf_rcca_req_type=equals&cf_rcca_done_type=equals&cf_rcca_sign_off_type=equals&cf_no_req_details_type=anywordssubstr&cf_no_req_details=&cf_feature_details_type=anywordssubstr&cf_feature_details=&cf_documentation_details_type=anywordssubstr&cf_documentation_details=&cf_other_details_type=anywordssubstr&cf_other_details=&cf_security_type=equals&cf_cwe_type=&cf_viss_type=&changedin=&chfieldfrom=&chfieldto=Now&chfieldoldvalue=&changes_from_product_name=0&changes_from_version_name=&chfieldvalue=&changes_to_product_name=0&changes_to_version_name=&bugidtype=include&bug_id=&votes=&sr_type=equals&sr=&sr_count_type=equals&sr_count=&cases_type=equals&cases=&case_count_type=equals&case_count=&wolken_cases_type=equals&wolken_cases=&wolken_case_count_type=equals&wolken_case_count=&jira_sds_type=equals&jira_sds=&jira_sd_count_type=equals&jira_sd_count=&kb_type=equals&kb=&kb_count_type=equals&kb_count=&field0-0-0=fix_by_version_name&type0-0-0=equals&value0-0-0=main&field0-1-0=category&type0-1-0=equals&value0-1-0=VSAN&field0-1-1=product&type0-1-1=equals&value0-1-1=VSAN&field0-1-2=category&type0-1-2=equals&value0-1-2=vSAN+File+Services&field0-1-3=category&type0-1-3=equals&value0-1-3=VDFS&field0-2-0=component&type0-2-0=notequals&value0-2-0=SnapService&field0-3-0=component&type0-3-0=notequals&value0-3-0=Automation&field0-4-0=component&type0-4-0=notequals&value0-4-0=SnapService+Appliance&field0-5-0=component&type0-5-0=notequals&value0-5-0=Tracing&field0-6-0=component&type0-6-0=notequals&value0-6-0=Active+Directory&field0-7-0=component&type0-7-0=nowords&value0-7-0=Documentation%2CBuild&field0-8-0=cf_type&type0-8-0=notequals&value0-8-0=Documentation&field0-9-0=cf_type&type0-9-0=notequals&value0-9-0=Task&field0-10-0=component&type0-10-0=notequals&value0-10-0=Tests&field0-11-0=component&type0-11-0=notequals&value0-11-0=SKY&field0-12-0=component&type0-12-0=notequals&value0-12-0=SnapService&field0-13-0=component&type0-13-0=notequals&value0-13-0=Humbug&field0-14-0=component&type0-14-0=notequals&value0-14-0=zeta&field1-0-0=keywords&type1-0-0=nowordssubstr&value1-0-0=vsan-90u1-release&field1-1-0=fix_by_version_name&type1-1-0=notequals&value1-1-0=Future&cmdtype=doit&columnlist=creation_ts%2Cdelta_ts%2Cpriority%2Cbug_status%2Cresolution%2Cassigned_to%2Creporter%2Ccomponent%2Ckeywords%2Cfix_by%2Ccf_eta%2Cshort_desc&backButton=true&textSaver=chfieldto%3DNow%7Cvalue0-0-0%3Dmain%7Cvalue0-1-0%3DVSAN%7Cvalue0-1-1%3DVSAN%7Cvalue0-1-2%3DvSAN%2520File%2520Services%7Cvalue0-1-3%3DVDFS%7Cvalue0-2-0%3DSnapService%7Cvalue0-3-0%3DAutomation%7Cvalue0-4-0%3DSnapService%2520Appliance%7Cvalue0-5-0%3DTracing%7Cvalue0-6-0%3DActive%2520Directory%7Cvalue0-7-0%3DDocumentation%252CBuild%7Cvalue0-8-0%3DDocumentation%7Cvalue0-9-0%3DTask%7Cvalue0-10-0%3DTests%7Cvalue0-11-0%3DSKY%7Cvalue0-12-0%3DSnapService%7Cvalue0-13-0%3DHumbug%7Cvalue0-14-0%3Dzeta%7Cvalue1-0-0%3Dvsan-90u1-release%7Cvalue1-1-0%3DFuture%7C&checkboxSaver=sPeople%3D000000000000000000000000%7CsBooleanSearch%3D00%7C&keywords=vsan-svs&keywords=vsan-svs-get-well&keywords=vsan-90u1-release&keywords=testissues&keywords=vsan-esa-dedup&keywords=vsan-90-opportunistic
```

- Examining the data in Redis
```
$ redis-cli
127.0.0.1:6379> json.get :src.schema.Url:01J34QN2VYKGNQYJ8JAZRHZ1ZZ
"{\"pk\":\"01J34QN2VYKGNQYJ8JAZRHZ1ZZ\",\"original_url\":\"https://bugzilla.eng.vmware.com/report.cgi?format=table&action=wrap&x_axis_field=component&y_axis_field=&z_axis_field=&query_format=report-table&ctype=&short_desc_type=allwordssubstr&short_desc=&longdesc_type=allwordssubstr&longdesc=&keywords_type=nowords&keywords=&target_milestone_type=allwords&target_milestone=&product=ESX&bug_status=new&bug_status=assigned&bug_status=reopened&priority=---&priority=P0&priority=P1&priority=P2&cf_build_type=equals&cf_build=&cf_branch_type=anywordssubstr&cf_branch=&cf_build_types_type=anywordssubstr&cf_build_types=&cf_build_target_type=anywordssubstr&cf_build_target=&cf_change_type=anywordssubstr&cf_change=&cf_test_id_type=equals&cf_test_id=&emailtype1=exact&email1=&emailtype2=exact&email2=&cf_type=Defect&cf_failed_type=equals&cf_failed=&cf_attempted_type=equals&cf_attempted=&cf_eta_type=&cf_doc_impact_type=equals&cf_i18n_impact_type=equals&host_op_sys_type=anyexact&guest_op_sys_type=anyexact&cf_jira_sync_type=equals&cf_rank_type=&cf_gss_rank_type=&cf_overall_update_type=anywordssubstr&cf_overall_update=&cf_rcca_req_type=equals&cf_rcca_done_type=equals&cf_rcca_sign_off_type=equals&cf_no_req_details_type=anywordssubstr&cf_no_req_details=&cf_feature_details_type=anywordssubstr&cf_feature_details=&cf_documentation_details_type=anywordssubstr&cf_documentation_details=&cf_other_details_type=anywordssubstr&cf_other_details=&cf_security_type=equals&cf_cwe_type=&cf_viss_type=&changedin=&chfieldfrom=&chfieldto=Now&chfieldoldvalue=&changes_from_product_name=0&changes_from_version_name=&chfieldvalue=&changes_to_product_name=0&changes_to_version_name=&bugidtype=include&bug_id=&votes=&sr_type=equals&sr=&sr_count_type=equals&sr_count=&cases_type=equals&cases=&case_count_type=equals&case_count=&wolken_cases_type=equals&wolken_cases=&wolken_case_count_type=equals&wolken_case_count=&jira_sds_type=equals&jira_sds=&jira_sd_count_type=equals&jira_sd_count=&kb_type=equals&kb=&kb_count_type=equals&kb_count=&field0-0-0=fix_by_version_name&type0-0-0=equals&value0-0-0=main&field0-1-0=category&type0-1-0=equals&value0-1-0=VSAN&field0-1-1=product&type0-1-1=equals&value0-1-1=VSAN&field0-1-2=category&type0-1-2=equals&value0-1-2=vSAN+File+Services&field0-1-3=category&type0-1-3=equals&value0-1-3=VDFS&field0-2-0=component&type0-2-0=notequals&value0-2-0=SnapService&field0-3-0=component&type0-3-0=notequals&value0-3-0=Automation&field0-4-0=component&type0-4-0=notequals&value0-4-0=SnapService+Appliance&field0-5-0=component&type0-5-0=notequals&value0-5-0=Tracing&field0-6-0=component&type0-6-0=notequals&value0-6-0=Active+Directory&field0-7-0=component&type0-7-0=nowords&value0-7-0=Documentation%2CBuild&field0-8-0=cf_type&type0-8-0=notequals&value0-8-0=Documentation&field0-9-0=cf_type&type0-9-0=notequals&value0-9-0=Task&field0-10-0=component&type0-10-0=notequals&value0-10-0=Tests&field0-11-0=component&type0-11-0=notequals&value0-11-0=SKY&field0-12-0=component&type0-12-0=notequals&value0-12-0=SnapService&field0-13-0=component&type0-13-0=notequals&value0-13-0=Humbug&field0-14-0=component&type0-14-0=notequals&value0-14-0=zeta&field1-0-0=keywords&type1-0-0=nowordssubstr&value1-0-0=vsan-90u1-release&field1-1-0=fix_by_version_name&type1-1-0=notequals&value1-1-0=Future&cmdtype=doit&columnlist=creation_ts%2Cdelta_ts%2Cpriority%2Cbug_status%2Cresolution%2Cassigned_to%2Creporter%2Ccomponent%2Ckeywords%2Cfix_by%2Ccf_eta%2Cshort_desc&backButton=true&textSaver=chfieldto%3DNow%7Cvalue0-0-0%3Dmain%7Cvalue0-1-0%3DVSAN%7Cvalue0-1-1%3DVSAN%7Cvalue0-1-2%3DvSAN%2520File%2520Services%7Cvalue0-1-3%3DVDFS%7Cvalue0-2-0%3DSnapService%7Cvalue0-3-0%3DAutomation%7Cvalue0-4-0%3DSnapService%2520Appliance%7Cvalue0-5-0%3DTracing%7Cvalue0-6-0%3DActive%2520Directory%7Cvalue0-7-0%3DDocumentation%252CBuild%7Cvalue0-8-0%3DDocumentation%7Cvalue0-9-0%3DTask%7Cvalue0-10-0%3DTests%7Cvalue0-11-0%3DSKY%7Cvalue0-12-0%3DSnapService%7Cvalue0-13-0%3DHumbug%7Cvalue0-14-0%3Dzeta%7Cvalue1-0-0%3Dvsan-90u1-release%7Cvalue1-1-0%3DFuture%7C&checkboxSaver=sPeople%3D000000000000000000000000%7CsBooleanSearch%3D00%7C&keywords=vsan-svs&keywords=vsan-svs-get-well&keywords=vsan-90u1-release&keywords=testissues&keywords=vsan-esa-dedup&keywords=vsan-90-opportunistic\",\"short_url\":\"http://127.0.0.1:5000/cc3ZY\",\"create_at\":\"2024-07-19\",\"expire_time\":\"2024-07-18\",\"alias_short_url\":\"\",\"user_id\":null}"

```

- Connect to the redis db on production
way1:
```
$ redis-cli -h localhost -p 10001 -a shorturl
Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.
localhost:10001> json.get :src.schema.Url:01J50VTM51AYC96DFYGBVXHYA0
"{\"pk\":\"01J50VTM51AYC96DFYGBVXHYA0\",\"original_url\":\"https://bugzilla.eng.vmware.com/buglist.cgi?action=wrap&backButton=true&bug_id=&bug_status=new&bug_status=assigned&bug_status=reopened&bugidtype=include&case_count=&case_count_type=equals&cases=&cases_type=equals&cf_attempted=&cf_attempted_type=equals&cf_branch=&cf_branch_type=anywordssubstr&cf_build=&cf_build_target=&cf_build_target_type=anywordssubstr&cf_build_type=equals&cf_build_types=&cf_build_types_type=anywordssubstr&cf_change=&cf_change_type=anywordssubstr&cf_cwe_type=&cf_doc_impact_type=equals&cf_documentation_details=&cf_documentation_details_type=anywordssubstr&cf_eta_type=&cf_failed=&cf_failed_type=equals&cf_feature_details=&cf_feature_details_type=anywordssubstr&cf_gss_rank_type=&cf_i18n_impact_type=equals&cf_jira_sync_type=equals&cf_no_req_details=&cf_no_req_details_type=anywordssubstr&cf_other_details=&cf_other_details_type=anywordssubstr&cf_overall_update=&cf_overall_update_type=anywordssubstr&cf_rank_type=&cf_rcca_done_type=equals&cf_rcca_req_type=equals&cf_rcca_sign_off_type=equals&cf_security_type=equals&cf_test_id=&cf_test_id_type=equals&cf_viss_type=&changedin=&changes_from_product_name=0&changes_from_version_name=&changes_to_product_name=0&changes_to_version_name=&checkboxSaver=sPeople%3D100000000001010010010000%7CsBooleanSearch%3D0%7C&chfieldfrom=&chfieldoldvalue=&chfieldto=Now&chfieldvalue=&cmdtype=doit&columnlist=creation_ts%2Cdelta_ts%2Cpriority%2Cbug_status%2Cresolution%2Cassigned_to%2Creporter%2Ccomponent%2Ckeywords%2Cfix_by%2Ccf_eta%2Cshort_desc&email1=&email2=&emailassigned_to1=1&emailassigned_to2=1&emailcc2=1&emailqa_contact2=1&emailreporter2=1&emailtype1=exact&emailtype2=exact&field0-0-0=noop&guest_op_sys_type=anyexact&host_op_sys_type=anyexact&jira_sd_count=&jira_sd_count_type=equals&jira_sds=&jira_sds_type=equals&kb=&kb_count=&kb_count_type=equals&kb_type=equals&keywords=&keywords=st-vsan-mustfix&keywords=st-vsan-90&keywords=st-vsan-reg-test&keywords_type=allwords&longdesc=&longdesc_type=allwordssubstr&short_desc=&short_desc_type=allwordssubstr&sr=&sr_count=&sr_count_type=equals&sr_type=equals&target_milestone=&target_milestone_type=allwords&textSaver=chfieldto%3DNow%7C&type0-0-0=noop&value0-0-0=&votes=&wolken_case_count=&wolken_case_count_type=equals&wolken_cases=&wolken_cases_type=equals&=&component=MCE\",\"hash_original\":\"f416111a42c23cd41676ff4ac263159ae3f566e12322afbe4765f93debac9500\",\"short_key\":\"Bav7T\",\"create_at\":\"2024-08-11\",\"expire_time\":null,\"user_id\":\"svc.vsan-er\"}"
```
way2: no warning
```
$ export REDISCLI_AUTH=shorturl
$ redis-cli -h localhost -p 10001
```
way3:
```
$ docker exec -it redis redis-cli -p 6379 -a shorturl
Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.
```
- Simple commands in Redis
1. Show all keys
```
keys *
```
2. Show all existing indexes
```
FT._LIST
```
3. Query all keys and delete one
```
127.0.0.1:6379> keys *
...
196) ":schema.Url:01J3Q70RMA08YRW23R5AXNK1CG"
197) ":schema.Url:01J34D8KBFXA6HQZXK9CT3E6V0"
localhost:6379> DEL key :schema.Url:01J3Q70RMA08YRW23R5AXNK1CG
(integer) 1
127.0.0.1:6379> keys *
...
196) ":schema.Url:01J34D8KBFXA6HQZXK9CT3E6V0"
```
4. Query all indexes and delete deactivated one
```
localhost:6379> FT._LIST
1) :src.schema.Url:index
2) :schema.Url:index
localhost:6379> FT.DROPINDEX :schema.Url:index
OK
localhost:6379> FT._LIST
1) :src.schema.Url:index
```

More redis commands see [Redis Commands](https://redis.io/docs/latest/commands/)

## Confluence Page

[Short URL Service](https://confluence.eng.vmware.com/pages/viewpage.action?spaceKey=~xiangyu&title=Short+URL+Service)

## Reference

[Nano ID](https://pypi.org/project/nanoid/)

[Redis-OM](https://pypi.org/project/redis-om/)

[RedisOM for Python](https://redis.io/docs/latest/integrate/redisom-for-python/)

[Redis OM Python Flask Starter Application](https://github.com/redis-developer/redis-om-python-flask-skeleton-app)

[Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)

[Redis import/export data by Local mount point](https://redis.io/docs/latest/operate/rs/databases/import-export/import-data/)
