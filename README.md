# control-tower

Instructions

1) Place the contents of the 'cloudformation' and 'lambda' files into an S3 bucket with PUBLIC read only permissions.

2) Download the crwd_manage_stacks_lambda.zip file.  Unzip the file and note the location of the stackset.  
Falcon_Discover_Url = https://ctstagingireland.s3-eu-west-1.amazonaws.com/crowdstrike_role_creation_ss.yaml  
You may modify this entry to the URL of the file in your S3 bucket. 

3) Recompress the file and upload to your s3 bucket.

4) Goto the Falcon Console and generate new OAuth2 ClientID and Client Secret API keys

4) Open Cloudformation in the master account of your control tower environment.  Load the template file 'ct_falcon_setup.yaml'

See the documentation folder for more inforamtion