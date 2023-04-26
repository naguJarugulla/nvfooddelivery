from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(userid,seconds):
    s=Serializer('23efgbnjuytr',seconds)
    return s.dumps({'admin':userid}).decode('utf-8')

