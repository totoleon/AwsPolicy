import json, boto3, re
from copy import deepcopy

class Statement(object):
    def __init__(self, statement, source_policy):
        self.__fields = ['Sid', 'Effect', 'Principal', 'Action','Resource', 'Condition']
        self.__ori_statement = deepcopy(statement)
        self.__changing_statement = statement
        self.source_policy = source_policy
        self.reload()
        self.validate()
    def validate(self):
        if type(self.content) is not dict:
            raise ValueError('Error parsing statement. Input is not a valid JSON object.')
    def save(self):
        for field in self.content.keys():
            if getattr(self, field) is not None:
                self.__changing_statement[field] = getattr(self, field)
            else:
                del self.__changing_statement[field]
        self.__ori_statement = deepcopy(self.__changing_statement)
        self.reload()
        return True
    def reload(self):
        self.content = deepcopy(self.__ori_statement)
        for field in self.__fields:
            setattr(self, field, self.content.get(field, None))

class PolicyBase(object):
    def __init__(self, **kwargs):
        ''' resourceIdentifer: CMK Id or Arn, S3 Bucket Name etc.
            serviceModule: e.g. boto3.client('kms'), session.client('kms'), boto3.client('s3') etc.
        '''
        self.__serviceModule = kwargs['serviceModule']
        self.__resourceIdentifer = kwargs['resourceIdentifer']
        self.reload()
        self.validate()
        self.sids = [ statement.get('Sid', '') for statement in self.Statement ]
    def validate(self):
        if type(self.content) is not dict:
            raise ValueError('Error parsing policy. Input is not a valid JSON object.')
    def fill_up_sids(self):
        c = 0
        for statement in self.Statement:
            if not statement.get('Sid', None):
                statement['Sid'] = 'statement' + str(c)
            c += 1
        self.save()
    def __is_principal_valid(self, p):
        # Identifying valid principals. Deleted principal will be something like AIDAJQABLZS4A3QDU576Q
        if re.compile("[A-Z0-9]{21}").match(p):
            return False
        else:
            return True
    def clean_up_deleted_principals(self):
        for statement in self.Statement:
            principal = statement.get('Principal')
            if type(principal) is dict:
                aws_principals = principal.get('AWS')
                if type(aws_principals) is not list:
                    aws_principals = [aws_principals]
                if aws_principals:
                    valid_aws_principals = [ p for p in aws_principals if self.__is_principal_valid(p) ]
                    if len(valid_aws_principals) == 0:
                        raise ValueError('Statement {} has no valid AWS principal').format(str(statement))
                    else:
                        principal['AWS'] = valid_aws_principals
    def select_statement(self, sid):
        searching = [ statement for statement in self.Statement if statement.get('Sid', None) == sid ]
        if len(searching) == 0:
            return None
        else:
            return Statement(searching[0], self)
    def reload(self):
        self.content = self.get_policy()
        self.__fields = self.content.keys()
        for field in self.__fields:
            setattr(self, field, self.content.get(field, None))
    def save(self, clean_deleted_principals=False):
        self.validate()
        if clean_deleted_principals:
            self.clean_up_deleted_principals()
        policy_string = json.dumps(self.content)
        resp = self.put_policy(policy_string)
        self.reload()
        return resp

class KmsPolicy(PolicyBase):
    def __init__(self, **kwargs):
        super(KmsPolicy,self).__init__(**kwargs)
    def get_policy(self):
        resp = self._PolicyBase__serviceModule.get_key_policy(KeyId=self._PolicyBase__resourceIdentifer, PolicyName='default')
        return json.loads(resp['Policy'])
    def put_policy(self, policy_string):
        resp = self._PolicyBase__serviceModule.put_key_policy(KeyId=self._PolicyBase__resourceIdentifer, PolicyName='default', Policy=policy_string)
        return resp

class BucketPolicy(PolicyBase):
    def __init__(self, **kwargs):
        super(BucketPolicy,self).__init__(**kwargs)
    def get_policy(self):
        resp = self._PolicyBase__serviceModule.get_bucket_policy(Bucket=self._PolicyBase__resourceIdentifer)
        return json.loads(resp['Policy'])
    def put_policy(self, policy_string):
        resp = self._PolicyBase__serviceModule.put_bucket_policy(Bucket=self._PolicyBase__resourceIdentifer, Policy=policy_string)
        return resp

class IamRoleTrustPolicy(PolicyBase):
    def __init__(self, **kwargs):
        super(IamRoleTrustPolicy,self).__init__(**kwargs)
    def get_policy(self):
        resp = self._PolicyBase__serviceModule.get_role(RoleName=self._PolicyBase__resourceIdentifer)
        return resp['Role']['AssumeRolePolicyDocument']
    def put_policy(self, policy_string):
        resp = self._PolicyBase__serviceModule.update_assume_role_policy(RoleName=self._PolicyBase__resourceIdentifer, PolicyDocument=policy_string)
        return resp