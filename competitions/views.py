from django.contrib import messages
import math
import random
from django.shortcuts import render
from .models import *

def generate_seed_array(round_num):
    #Triangular array read by rows in bracket pairs
    #https://oeis.org/A208569  
    def T(n, k):
        if n == 1 and k == 1:
            return 1
        
        elif k % 2 == 1:
            return T(n - 1, (k + 1) // 2)
            
        return 2**(n - 1) + 1 - T(n - 1, k // 2)

    return [T(round_num+1, k) for k in range(1, 2**(round_num) + 1)]


def BracketView(request, bracket_id):
    t = ""

    numTeams = 32
    numRounds = math.ceil(math.log(numTeams, 2))

    seed_array = generate_seed_array(numRounds)

    roundWidth = 175
    connectorWidth = 50
    bracketWidth = (roundWidth+connectorWidth)*numRounds
    bracketHeight = numTeams/0.02
    roundHeight = bracketHeight

    t += f'<div class="bracket" style="height: {bracketHeight}px; width: {bracketWidth}px;">'    

    for i in range(0,numRounds):
        t += f'<div class="round" style="height: {roundHeight}px; width: {roundWidth}px;">'

        numMatches = 2**(numRounds-i-1)
        matchHeight = roundHeight/numMatches
        matchWidth = roundWidth

        for j in range(0, numMatches):

            numTeams = 2
            teamHeight = 25
            centerHeight = teamHeight*numTeams
            topPadding = (matchHeight-centerHeight)/2

            t += f'<div class="match" style="height: {matchHeight}px; width: {matchWidth}px;">'
            t += f'<div class="center" style="height: {centerHeight}px; padding-top: {topPadding}px">'

            for k in range(0,numTeams):
                t += f'<div class="team" style="width: {matchWidth}px;">{f"Seed {seed_array[2*j + k]}" if i == 0 else "TBD"}</div>'
            
            t += f'</div></div>'
        t += '</div>'
    t += '</div>'

    context = {"content":t}
    return render(request, "competitions/bracket.html", context)