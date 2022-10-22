# faire des stats sur des jeux de cartes pas trop compliqués

from curses import A_ALTCHARSET
from http.cookiejar import FileCookieJar
from platform import java_ver
from time import sleep, time_ns
import numpy as np

from random import shuffle, seed

from yaml import FlowSequenceEndToken

from matplotlib import pyplot as plt


BLACK = 0
RED = 1

# ces constantes sont choisies pour correspondre au code UTF8 correspondant
# https://en.wikipedia.org/wiki/Playing_cards_in_Unicode
HEARTS = "B"   # coeurs
CLUBS = "D"    # trèfles
DIAMONDS = "C" # diamants
SPADES = "A"   # piques

# inutilisé
HEARTS_CHAR = "♥"
CLUBS_CHAR = "♣"
DIAMONDS_CHAR = "♦"
SPADES_CHAR = "♠"


# prend un string contenant un code utf8, par exemple "1F0A1"
# et renvois un entier qui, passé dans chr(), met le bon caractère utf8
def get_chr_val(a):
    val=0
    p16 = 1
    for c in reversed(a):
        val += int(c,16)*p16
        p16 *= 16
    return val

INDEXES = {
    'S' :0, # JOCKER
    '1' :1,
    'A' :1,
    '2' :2,
    '3' :3,
    '4' :4,
    '5' :5,
    '6' :6,
    '7' :7,
    '8' :8,
    '9' :9,
    '10':10,
    '11':11,
    'V' :11,
    'J' :11,
    '12':12, # "Knight" représenté avec un C (??)
    '13':13,
    'D' :13,
    'Q' :13,
    '14':14,
    'R' :14,
    'K' :14
}

class Card:
    def __init__(self, type = HEARTS, index = INDEXES['J'], color = BLACK, facecachee=False):
        self.type= type
        self.index = index
        self.color = BLACK if (type==SPADES or type==CLUBS) else RED
        self.facecachee=facecachee # est ce que la carte est visible par le joueur
        pass

    def __str__(self):
        # repr = HEARTS_CHAR if self.type==HEARTS else CLUBS_CHAR if self.type==CLUBS else DIAMONDS_CHAR if self.type==DIAMONDS else SPADES_CHAR
        # if self.color == BLACK:
        #     return self.index + " " + repr
        # else:
        #     return "\e[91m" + self.index + " " + repr + "\e[0m"
        c = "1F0" + self.type + hex(self.index)[-1]
        return ("\033[91m" if self.color==RED else "") + chr(get_chr_val(c)) + ("\033[0m" if self.color==RED else "")

class LengthMetaclass(type):
    def __len__(self):
        return self.clslength()

# contient la main d'un joueur
class Hand:
    def __init__(self, cards):
        self.cards = cards.copy() # copie locale
    
    # mélange la main
    def melange(self):
        shuffle(self.cards)
    
    # renvois la ieme carte du jeu, SANS LA SORTIR de la main
    # si i n'est pas précisé, renvois la première carte
    def get_card(self,i=0):
        if i < 0 or i >= len(self.cards):
            print("erreur get_card : index invalide :", i)
            return None
        return self.cards[i]
    
    # renvois la ieme carte du jeu, EN LA SORTANT de la main
    # si i n'est pas précisé, prend la première carte
    def pop_card(self,i=0):
        if i < 0 or i >= len(self.cards):
            print("erreur pop_card : index invalide :", i)
            return None
        return self.cards.pop(i)

    # insere une carte dans la main
    # si i=-1 (par défaut), la carte est ajoutée à la fin de la main
    # sinon elle est ajoutée telle que la carte à ajouter soit dans self.cards[i]
    def insert_card(self,card,i=-1):
        if i<0 or i >= len(self.cards):
            self.cards.append(card)
        else:
            self.cards[i:i] = [card]

    def print(self):
        for card in self.cards:
            print(str(card) + " ", end="")
        print("\n")
    
    def __len__(self):
        return len(self.cards)


class Game:
    def __init__(self):
        self.cards = []
        for type in [HEARTS, CLUBS, DIAMONDS, SPADES]:
            for index in range(1,15):
                if index!=12:  # on saute ce ptn de "cavalier"
                    self.cards.append(Card(type, index))

        ## la valeur qui interrompt le jeu, si elle est renvoyée par loop
        self.loop_end = 0 
        
        ## la valeur qui fait que le jeu continue après une loop
        self.loop_continue = 1
        
        # temps d'attente entre deux loop, en ms (0 pour désactivé)
        self.delayms = 0

    def loop(self):
        return self.loop_end 

    def start_game(self):
        while self.loop() == self.loop_continue:
            if self.delayms:
                sleep(self.delayms/1000)
        self.game_end()


    def game_end(self):
        pass



class Bataille(Game):
    def __init__(self):
        super().__init__() # parent's __init__

        shuffle(self.cards)

        # for card in self.cards:
        #     print(str(card) +" ", end="")
        #     # if(card.index == 14): print("\n")
        # print("\n")
        
        self.p1 = Hand(self.cards[:26])
        self.p2 = Hand(self.cards[26:])

        # self.p1.print()
        # self.p2.print()

        self.bataille = {}
        for i in range(13):
            self.bataille[i] = 0

        self.tours = 0
    # renvois une liste des cartes sorties de chaques jeux, ainsi que qui a gagné
    # sous la forme [ <gagnant>, [<cartes du joueur 1>], [<cartes du joueur 2>]]
    # gagnant = 1 si joueur 1 gagne
    #         = 2 si joueur 2 gagne
    #         = -1 si égalité (pat)
    def aux_bagarre(self, card1, card2, depth=0):
        self.bataille[depth]+=1
        # print("bagarre niveau {} ! ".format(depth), card1, "vs", card2)
        cartej1 = []
        cartej2 = []
        if depth==0: cartej1 = [card1]
        if depth==0: cartej2 = [card2]
        if len(self.p1) < 2 or len(self.p2) < 2:
            return [-1, cartej1, cartej2]
        cachee1 = self.p1.pop_card(0)
        cachee2 = self.p2.pop_card(0)
        nv1 = self.p1.pop_card(0)
        nv2 = self.p2.pop_card(0)
        cartej1 += [cachee1, nv1]
        cartej2 += [cachee2, nv2]
        addcartej1 = []
        addcartej2 = []
        if nv1.index < nv2.index:
            gagnant = 2
        elif nv1.index > nv2.index:
            gagnant = 1
        else:
            gagnant, addcartej1, addcartej2 = self.aux_bagarre(nv1, nv2, depth+1)
        
        return gagnant, cartej1+addcartej1, cartej2+addcartej2

    def loop(self):
        self.tours+=1
        # if self.tours%100==0 or len(self.p1) < 3 or len(self.p2) < 3: print("tour : {}, p1={}, p2={}".format(self.tours,len(self.p1), len(self.p2)))
        # if self.tours%100==0: print("tour : {}, p1={}, p2={}".format(self.tours,len(self.p1), len(self.p2)))
        
        card1 = self.p1.pop_card(0)
        card2 = self.p2.pop_card(0)

        if card1.index < card2.index:
            self.p2.insert_card(card1)
            self.p2.insert_card(card2)
        elif card1.index > card2.index:
            self.p1.insert_card(card2)
            self.p1.insert_card(card1)
        else:
            # print("bagarre ! ", card1, "vs", card2, " (pas fait)")
            # self.p1.insert_card(card1)
            # self.p2.insert_card(card2)
            gagnant, cartej1, cartej2 = self.aux_bagarre(card1, card2)

            if gagnant == -1:
                for card1,card2 in zip(cartej1,cartej2):
                    self.p1.insert_card(card1)
                    self.p2.insert_card(card2)
                return self.loop_end
            elif gagnant == 1:
                for card1, card2 in zip(cartej1, cartej2):
                    self.p1.insert_card(card1)
                    self.p1.insert_card(card2)
            elif gagnant == 2:
                for card1, card2 in zip(cartej1, cartej2):
                    self.p2.insert_card(card1)
                    self.p2.insert_card(card2)
            else:
                print("bizarre")
                return self.loop_end


        if len(self.p1) == 0 or len(self.p2) == 0:
            return self.loop_end
        return self.loop_continue

    # def game_end(self):
    #     print("p1 : ",end="")
    #     self.p1.print()
    #     print("p2 : ",end="")
    #     self.p2.print()
    #     if len(self.p1) == 0:
    #         print("Le joueur 2 a gagné en {} tours !".format(self.tours))
    #     elif len(self.p2) == 0:
    #         print("Le joueur 1 a gagné en {} tours !".format(self.tours))
    #     else:
    #         print("Égalité en {} tours ! ({},{})".format(self.tours, len(self.p1), len(self.p2)))       
    


if __name__ == '__main__':

    seed_rng = time_ns()
    # seed_rng = 1
    seed(seed_rng) 

    # card = Card(SPADES, INDEXES.get('8'), BLACK)
    # print(card)

    # g = Game()
    # for card in g.cards:
    #     print(str(card) +" ", end="")
    #     if(card.index == 14): print("\n")

    # g = Bataille()
    # g.start_game()
    # print(g.bataille)

    somme_tour = 0
    somme_bataille = {}
    list_bataille = {}

    moy_pourcentage_bataille = []
    

    nb_pat = 0

    for i in range(13):
        somme_bataille[i] = 0
        list_bataille[i] = []

    iter = 10000
    lst_tour = []
    for i in range(iter):

        g = Bataille()
        g.start_game()
        somme_tour+=g.tours

        lst_tour.append(g.tours)

        for key,val in g.bataille.items():
            somme_bataille[key] += val
            list_bataille[key].append(val)

        moy_pourcentage_bataille.append((100*g.bataille[0]/g.tours))

        if len(g.p1) != 0 and len(g.p2) != 0:
            nb_pat+=1

    print(f"{nb_pat=}/{iter}")
    plt.figure()
    # plt.hist(list_bataille[0], 15, alpha=0.4)
    plt.plot(lst_tour, list_bataille[0], "+")
    
    plt.figure()
    moy_pourcentage_bataille.sort()
    # plt.plot(range(iter), moy_pourcentage_bataille)
    plt.hist(moy_pourcentage_bataille, 50)

    print("moyenne de nombre de tours : {}".format(somme_tour/iter))
    print("batailles : ")
    for key,val in somme_bataille.items():
        val
        if val != 0:
            print("bataille niveau {} : {} ({}%)".format(key+1, val/iter, round(100*val/somme_tour,2)))


    # plt.figure()
    # plt.hist(lst_tour, 50)
    print(f"{np.median(lst_tour)=}")
    # lst_tour.sort()
    # plt.plot(range(iter), lst_tour, "+")
    plt.show()