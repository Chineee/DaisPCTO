def checkPasswordNumber(password):
        isNumber = False
        for number in password:
            if number.isdigit():
                isNumber = True
        return isNumber 

def checkPasswordCaps(password):
    isCaps = False
    for char in password:
        if char in ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']:
            isCaps = True
    return isCaps

def checkPasswordSpecial(password):
    isSpecial = False
    for char in password:
        if char in ['@','#','_','-','*','$','%','&','+','£']:
            isSpecial = True
    return isSpecial

def checkPasswordLength(password):
    return len(password) >= 8