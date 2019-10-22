This spec file is used when you need to deploy ansible-runner-service without SSL authentication
on the Apache. The only thing you need to do is to configure Apache as follows and Ansible runner
service will be running on port 5001, served by Apache:

```
Listen 5001
<VirtualHost _default_:5001>
    LogLevel debug
    WSGIDaemonProcess runner user=user group=user threads=2
    WSGIProcessGroup runner
    WSGIScriptAlias / /var/www/runner/runner.wsgi
    CustomLog "logs/ansible_runner_log" "%h %l %u %t \"%r\" %>s %b"
    ErrorLog "logs/ansible_runner_error_log"
</VirtualHost>
```

Where `/var/www/runner/runner.wsgi` is `wsgi.py` file copied from root of this repo.
