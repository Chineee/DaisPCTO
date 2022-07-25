def checkPasswordNumber(password):
        isNumber = False
        for number in password:
            if number.isdigit():
                isNumber = True
        return isNumber 

def checkPasswordCaps(password):
    isCaps = False
    for c in password:
        if c.isupper() == True:
            isCaps = True
    return isCaps

def checkPasswordSpecial(password):
    isSpecial = False
    for char in password:
        if char in ['@','_','-','*','$','%','&','+','£']:
            isSpecial = True
    return isSpecial

def checkPasswordLength(password):
    return len(password) >= 8
