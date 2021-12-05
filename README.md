Script that runs periodically PINGs and SSH sessions to peers to monitor network connectivity to each other hosts.
Periodically gathers PING results and the latest timestamps in dmesg via an SSH session. The following files are required:
    hostlist.json: containing dictionary with with key/value pairs of hostnames and ip addresses.
    .email_profile.log: containing sensitive information for email account and receipient addresses.
The script supervisor.py is tied to crontab and will run periodically where itself will invoke the actual script doing the pinging and sshing and use the mailer.py to send email according to the configuration setup in the .log file.
No additional libraries are needed.

