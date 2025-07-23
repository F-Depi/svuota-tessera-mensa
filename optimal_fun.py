import re
import numpy as np

"""
Funzioni per trovare la soluzione ottimale al problema della tessera della
mensa.
"""

snack = 3.10
ridotto = 4.40
intero = 4.90

multiplo_ricarica = 5

def posso_caricare_multiplo_5(a, b, c, credito) -> bool:
    ## Prezzi menù

    speso = a * snack + b * ridotto + c * intero
    caricare = round(speso - credito, 2)

    if caricare < 0:
        return False

    return caricare % multiplo_ricarica == 0


def find_solutions(credito, max_solutions = 10) -> np.ndarray | None:

    pasti_possibili = np.zeros([9999, 3], dtype=int)
    ii = 0

    S = 1  # minimal possible sum 

    # generate all (a,b,c) with a+b+c == S
    # 120 è stato scelto perché permette di trovare soluzioni fino a 500€ di
    # credito
    while S < 120 and ii < 10:
        if ii > 10:
            break
        for a in range(0, S + 1):
            for b in range(0, S - a + 1):
                c = S - a - b

                if posso_caricare_multiplo_5(a, b, c, credito):

                    pasti_possibili[ii, :] = (a, b, c) 
                    ii += 1
        S += 1
    
    if ii == 0:
        return None

    ## Tolgo gli 0, ordino le soluzioni e prendo le prime
    totals = pasti_possibili.sum(axis=1)

    result = np.c_[pasti_possibili, totals]
    result = result[result[:, 3] != 0]

    ricarica = np.int64(np.round(result[:,0] * snack + result[:, 1] * ridotto + result[:, 2] * intero - credito))
    result = np.c_[result, ricarica]
    result = result[np.lexsort((result[:, 3], result[:, 4]))]

    return result[:10, :]
