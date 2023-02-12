# Introduction
This is release 0.1.0.  It is a release that works for a single verse.

But it relies on undocumented internal files.  I do not recommend trying to use this project yet.

Please create an issue if you are thinking about using this.  Hopefully I get emailed...

# Command to show all timestamps in chronological order
ls *.json | tr -- '-.' '  ' | awk -n '{print $(NF-1)}' | sort | wc

# For future consideration
It might be better to create an access token than to have
a service account with credentials stored.
# https://stackoverflow.com/questions/60554732/gcp-impersonate-service-account-as-a-user

