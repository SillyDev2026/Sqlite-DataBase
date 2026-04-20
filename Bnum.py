import math
import random

class Bnum:
    def __init__(self, man: float, exp: int = 0):
        self.man = float(man)
        self.exp = int(exp)
        self.normalize()

    def normalize(self):
        if self.man == 0:
            self.exp = 0
            return self
        man = abs(self.man)
        shift = math.floor(math.log10(man))
        self.man = (1 if self.man > 0 else -1) * (man / (10**shift))
        self.exp += shift
        return self

    @classmethod
    def new(cls, man, exp):
        return cls(man, exp)

    @classmethod
    def fromNumber(cls, val):
        if val == 0:
            return cls(0, 0)

        sign = -1 if val < 0 else 1
        val = abs(val)

        exp = math.floor(math.log10(val))
        man = val / (10 ** exp)

        return cls(sign * man, exp)
    
    @classmethod
    def fromString(cls, val: str):
        val = val.strip().lower()
        if val in ("0", "0e0"):
            return cls(0, 0)
        if "e" not in val:
            return cls.fromNumber(float(val))
        base, exp = val.split("e", 1)
        base = float(base)
        exp = int(exp)
        total_exp = math.log10(abs(base)) + exp
        sign = -1 if base < 0 else 1
        man = sign * 10 ** (math.log10(abs(base))) - math.floor(math.log10(abs(base)))
        exp_final = math.floor(total_exp)
        man = sign * (abs(base))/(10**math.floor(math.log10(abs(base))))
        return cls(man, exp_final)
    
    @classmethod
    def fromTable(cls, val):
        if isinstance(val, (list, tuple)):
            if len(val) != 2:
                raise ValueError("Table must have exactly 2 elements: [man, exp]")
            man, exp = val
            return cls(man, exp)
        raise TypeError("fromTable ex[ects a list or tuple of length 2")
    
    @classmethod
    def convert(cls, val):
        if isinstance(val, cls):
            return val
        if isinstance(val, (list, tuple)):
            if len(val) == 2:
                return cls.fromTable(val)
            return cls(0, 0)
        
        if isinstance(val, str):
            try:
                return cls.fromString(val)
            except:
                return cls(0, 0)
            
        if isinstance(val, (int, float)):
            return cls.fromNumber(val)
        
        return cls(0, 0)
    
    @classmethod
    def add(cls, val1, val2):
        val1, val2 = cls.convert(val1), cls.convert(val2)
        if val1.man == 0:
            return val2
        if val2.man == 0:
            return val1
        if val1.exp > val2.exp:
            diff = val1.exp - val2.exp
            man1 = val1.man
            man2 = val2.man/(10**diff)
            exp = val1.exp
        else:
            diff = val2.exp-val1.exp
            man1 = val1.man/(10**diff)
            man2 = val2.man
            exp = val2.exp

        man = man1+man2
        result = cls.new(man, exp)
        return result
    
    @classmethod
    def sub(cls, val1, val2):
        val1, val2 = cls.convert(val1), cls.convert(val2)
        if val1.man == 0:
            return val2
        if val2.man == 0:
            return val1
        if val1.exp > val2.exp:
            diff = val1.exp - val2.exp
            man1 = val1.man
            man2 = val2.man/(10**diff)
            exp = val1.exp
        else:
            diff = val2.exp-val1.exp
            man1 = val1.man/(10**diff)
            man2 = val2.man
            exp = val2.exp
        man = man1-man2
        result = cls(man, exp)
        result.normalize()
        return result

    @classmethod
    def mul(cls, val1, val2):
        val1, val2 = cls.convert(val1), cls.convert(val2)
        if val1.man == 0 or val2.man == 0:
            return cls(0, 0)
        man = val1.man*val2.man
        exp = val1.exp+val2.exp
        return cls(man, exp)
    
    @classmethod
    def recip(cls, val):
        val = cls.convert(val)
        man = 1/val.man
        return cls(man, -val.exp)
    
    @classmethod
    def div(cls, val1, val2):
        result = cls.mul(val1, cls.recip(val2))
        return result
    
    @classmethod
    def logn(cls, val):
        val = cls.convert(val)
        if val.man < 0:
            raise ValueError("ln is only defined for positive numbers")
        
        result = math.log(abs(val.man)) + val.exp * 2.302585092994046
        return cls.fromNumber(result)
    
    @classmethod
    def log10(cls, val):
        val = cls.convert(val)
        if val.man <= 0:
            return cls(0, 0)
        result = math.log10(val.man) + val.exp
        if abs(result) < 10:
            return cls(result, 0)
        shift = math.floor(math.log10(abs(result)))
        man = result/(10**shift)
        exp = shift
        return cls(man, exp)
    
    @classmethod
    def log(cls, val1, val2):
        val1, val2 = cls.convert(val1), cls.convert(val2)
        if val2.man < 0:
            raise ValueError("Value 2 cant be < 0")
        return cls.div(cls.log10(val1), cls.log10(val2))
    
    @classmethod
    def pow(cls, val1, val2):
        val1, val2 = cls.convert(val1), cls.convert(val2)
        if val1.man <= 0:
            raise ValueError("val2 must be positivie")
        loga = cls.log10(val1)
        power = cls.mul(loga, val2)
        return cls.pow10(power)
    
    @classmethod
    def pow10(cls, val):
        val = cls.convert(val)
        if val.man == 0:
            return cls(1, 0)
        real_exp = val.man * (10**val.exp)
        exp = math.floor(real_exp)
        man = 10 ** (real_exp - exp)
        return cls(man, exp)
    
    @classmethod
    def suffix_part(index):
        firstset = ["", "U","D","T","Qd","Qn","Sx","Sp","Oc","No"]
        second   = ["", "De","Vt","Tg","qg","Qg","sg","Sg","Og","Ng"]
        third    = ["", "Ce","Du","Tr","Qa","Qi","Se","Si","Ot","Ni"]
        hund = index // 100
        index = index % 100
        ten = index//10
        one = index % 10
        return (
            (firstset[one] if one < len(firstset) else "") + 
            (second[ten] if ten < len(second) else "") + 
            (third[hund] if hund < len(third) else "")
        )
    
    @classmethod
    def format(cls, val, decimals=2):
        val = cls.convert(val)
        man = val.man
        exp = val.exp

        if man == 0:
            return "0"

        sign = "-" if man < 0 else ""
        man = abs(man)

        suffixes = ["", "k", "m", "b"]

    # normalize exponent into base-10 scientific style
        if exp < 3000:
            index = exp // 3
            lf = exp % 3

        # shift mantissa properly
            man = man * (10 ** lf)

        # scale into readable range
            while man >= 1000:
                man /= 1000
                index += 1

        # apply decimal precision
            man = round(man, decimals)

        # suffix handling
            if index < len(suffixes):
                return f"{sign}{man:.{decimals}f}{suffixes[index]}"

            suffix = index - 1
            return f"{sign}{man:.{decimals}f}{cls.suffix_part(suffix)}"

        else:
            exp_str = cls.format(cls.fromNumber(exp), decimals)
            return f"{sign}E{exp_str}"
    @classmethod
    def random(cls, val1, val2):
        if val1 is None and val2 is None:
            return cls.fromNumber(random.random())
        val1, val2 = cls.convert(val1), cls.convert(val2)
        if val1.man <= 0 or val2.man <= 0:
            return cls.fromNumber(random.random())
        loga = math.log10(val1.man)+val1.exp
        logb = math.log10(val2.man)+val2.exp
        r = loga+random.random()*(logb-loga)
        exp = math.floor(r)
        man = 10 ** (r-exp)
        return cls(man, exp)

    @classmethod
    def toNumber(cls, val):
        val = cls.convert(val)
        return val.man*(10**val.exp)
    
    @classmethod
    def numFloor(cls, val):
        return math.floor(cls.toNumber(val))

    @classmethod
    def cmp(cls, val1, val2):
        val1, val2 = cls.convert(val1), cls.convert(val2)
        if val1.man == val2.man and val1.exp == val2.exp:
            return 0
        if cls.le(val1, val2):
            return -1
        return 1
    
    @classmethod
    def le(cls, val1, val2):
        val1, val2 = cls.convert(val1), cls.convert(val2)
        if val1.man == 0 and val2.man == 0:
            return False
        if val1.man < 0 and val2.man >= 0:
            return True
        if val1.man >= 0 and val2.man < 0:
            return False
        if val1.exp != val2.exp:
            return val1.exp < val2.exp if val1.man > 0 else val1.exp > val2.exp
        return val1.man < val2.man
    
    @classmethod
    def eq(cls, val1, val2):
        val1, val2 = cls.convert(val1), cls.convert(val2)
        return val1.man == val2.man and val1.exp == val2.exp
    
    @classmethod
    def me(cls, val1, val2):
        return cls.cmp(val1, val2) == 1
    
    @classmethod
    def leeq(cls, val1, val2):
        return cls.cmp(val1, val2) <= 0
    
    @classmethod
    def meeq(cls, val1, val2):
        return cls.cmp(val1, val2) >= 0
    
    def __repr__(self):
        return f"{self.man}e{self.exp}"
    
    def __str__(self):
        return self.format(self)

    def to_dict(self):
        return {"man": self.man, "exp": self.exp}
    
    @classmethod
    def from_dict(cls, d):
        return cls(d["man"], d["exp"])
    
