# Modules to modify AWS resource based policies as an object based Sid
# Supported: KMS CMK policy, S3 bucket policy, IAM Role trust relationship

# Example usage in a snippet:
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
import json, boto3
from awspolicy import BucketPolicy, KmsPolicy, IamRoleTrustPolicy

iam = boto3.client('iam')
role_trust_policy = IamRoleTrustPolicy(serviceModule=iam, resourceIdentifer='EC2ReadOnly')
s = role_trust_policy.select_statement('CrossAccount')
s.Conditon = None
s.save()
s.source_policy.save()
