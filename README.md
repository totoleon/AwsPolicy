# A small package that helps modifying AWS policies as an object

AWS SDKs provides a wide availbility allowing automation and codifying your infrastructure. However, minipulating policies are not in a good control, because they are treated as a whole block of String.

Scenario 1. You have an S3 bucket in a centralized account, which grants write permission of CloudTrail logs from all other accounts. At onboarding of a new account, you need to modify the bucket policy to insert another trusted principal. Doing it manually is ugly and unsafe.

Scenario 2. In your billing account, there is an IAM Role that allows certain IAM Users to assume from the landing account. When a new IAM User is created and needed to be added to the trusted policy, you will need to update the policy manually.

The diffuculty of automating this process is that, you have to keep the integrity of your policy document and only change the part that you want to. That's what this package can help you do.

Borrowing the idea of selecting an element from HTML document, you can select a particular Statement from a policy document giving the Sid.

## Get started:
This package only provides classes that you can use in your own code. It depends on boto3 but does not install it for you.

To install the package:  
`pip install awspolicy`

## Examples:
Talk is cheap and lets code. I have an S3 bucket, which has the following policy that controls permissions from IAM users. At the moment, it only grants IAM User 'bob' and 'jack' permission of to get contents from directory 'admin_folder'. When a new admin user 'daniel' onboards, I need to add his IAM User ARN to be granted in the policy, while not interferring the other functions of the policy document. Here is an example code to achieve that. Before, by bucket policy in JSON is like this:

```
{
    "Id": "MyBucketPolicy",
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AutomatedRestrictiveAccess",
            "Action": [
                "s3:GetObject"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:s3:::hailong-python/admin_folder/*",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::888888888888:user/bob",
                    "arn:aws:iam::888888888888:user/jack"
                ]
            }
        },
        {
            "Sid": "GenerallyGrantingAccess",
            "Action": [
                "s3:GetObject"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:s3:::hailong-python/shared_files/*",
            "Principal": {
                "AWS": [
                    "888888888888"
                ]
            }
        },
        {
            "Sid": "DenyNonHTTPSTrafic",
            "Action": [
                "s3:*"
            ],
            "Effect": "Deny",
            "Resource": "arn:aws:s3:::hailong-python/*",
            "Principal": "*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
```

Example code to modify the policy in Python

```
import boto3
from awspolicy import BucketPolicy

s3_client = boto3.client('s3')
bucket_name = 'hailong-python'

# Load the bucket policy as an object
bucket_policy = BucketPolicy(serviceModule=s3_client, resourceIdentifer=bucket_name)

# Select the statement that will be modified
statement_to_modify = bucket_policy.select_statement('AutomatedRestrictiveAccess')

# Insert new_user_arn into the list of Principal['AWS']
new_user_arn = 'arn:aws:iam::888888888888:user/daniel'
statement_to_modify.Principal['AWS'].append(new_user_arn)

# Save change of the statement
statement_to_modify.save()

# Save change of the policy. This will update the bucket policy
statement_to_modify.source_policy.save() # Or bucket_policy.save()

```

After running the code, the new user is added to the statement:

```
{
    "Version": "2012-10-17",
    "Id": "MyBucketPolicy",
    "Statement": [
        {
            "Sid": "AutomatedRestrictiveAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::888888888888:user/daniel",
                    "arn:aws:iam::888888888888:user/jack",
                    "arn:aws:iam::888888888888:user/bob"
                ]
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::hailong-python/admin_folder/*"
        },
        {
            "Sid": "GenerallyGrantingAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::888888888888:root"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::hailong-python/shared_files/*"
        },
        {
            "Sid": "DenyNonHTTPSTrafic",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::hailong-python/*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
```

## More usages of the classes

```
# Policy
policy.fill_up_sids()           # Generate Sids to the statements that don't have one. This updates the policy documents
policy.select_statement(sid)    # Selecting a statement giving Sid. It returns None if didn't find one
policy.reload()                 # Reload the policy document. This triggers getting the policy from AWS
policy.save()                   # Upload the current policy document to AWS
policy.sids                     # A list of statement Ids of the policy
policy.content                  # Policy content in dict
policy.save(clean_deleted_principals=True)                   # Save the policy document. If there is any deleted resources it will clean it up from the malformatted policy
# Statement
statement.reload()              # Reconstruct the statement content from the loaded Policy
statement.save()                # Save changes of the statement
statement.content               # Statement content in dict
statement.source_policy         # Referring to the policy object which this statement belongs to
## Fields of the statement. In the type of dict or string
statement.Sid
statement.Effect
statement.Principal
statement.Action
statement.Resource
statement.Condition
```

### More example usages in a snippet:
```
# Modules to modify AWS resource based policies as an object based Sid
# Supported: KMS CMK policy, S3 bucket policy, IAM Role trust relationship

import json, boto3
from awspolicy import BucketPolicy, KmsPolicy, IamRoleTrustPolicy
### Update KMS Key policy to allow a new account using CMK in centralized auditing account
kms = boto3.client('kms')
cmk_policy = KmsPolicy(serviceModule=kms, resourceIdentifer='xxxxe011-a1ff-4460-8942-02da951xxxx')
statement = cmk_policy.select_statement('AllowCloudTrailEncryptCrossAccountLogs')
statement.Condition['StringLike']['kms:EncryptionContext:aws:cloudtrail:arn'] += [u'arn:aws:cloudtrail:*:888888888888:trail/*']
statement.save()
statement.source_policy.save()

### Update S3 bucket policy from a STS session to allow a new account using CMK in centralized auditing account
s3 = session.client('s3')
bucket_policy = BucketPolicy(serviceModule=s3, resourceIdentifer='hailong-cloudtrail')
statement = bucket_policy.select_statement('CloudTrailCrossAccountPermission')
to_add_resource = 'arn:aws:s3:::hailong-cloudtrail/AWSLogs/888888888888/*'
if to_add_resource not in statement.Resource:
    statement.Resource += ['arn:aws:s3:::hailong-cloudtrail/AWSLogs/888888888888/*']
    statement.save()
    statement.source_policy.save()

### Update IAM Role trusted relationship to remove Condition from a statement
iam = boto3.client('iam')
role_trust_policy = IamRoleTrustPolicy(serviceModule=iam, resourceIdentifer='EC2ReadOnly')
s = role_trust_policy.select_statement('CrossAccount')
s.Conditon = None
s.save()
s.source_policy.save()
```

## To do
This is a very simple package which I hope could help someone. If needed, we can wrap it up in a tool that allows more interactions with AWS policies. At this time, it only works with three kinds of Resource based policies S3, KMS, and IAM Role. With a bit of restructuring, it can be expanded to others like IAM principal-based policies etc. Please let me know if you found any bug or want to contribute.


