# Falcon Discover - Control Tower Setup

## Instructions

1) Place the contents of the 'cloudformation' and 'lambda' files into an S3 bucket and grant the objects PUBLIC read only permissions.

2) Goto the Falcon Console and generate new OAuth2 ClientID and Client Secret API keys

3) Open Cloudformation in the master account of your control tower environment.  Load the template file 'ct_crowdstrike_master_account.yaml'

3) Open Cloudformation in the log-archive account of your control tower environment.  Load the template file 'ct_crowdstrike_log_archive_account.yaml'

See the documentation folder for more information