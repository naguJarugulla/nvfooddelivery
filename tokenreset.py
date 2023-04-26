from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(username,seconds):
    s=Serializer('23efgbnjuytr',seconds)
    return s.dumps({'user':username}).decode('utf-8')
