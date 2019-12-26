#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np


# In[2]:


bbbsDF = pd.read_csv('Ball_by_Ball.csv')
bbbsDF = bbbsDF.apply(pd.to_numeric, axis=0)
matchesDF = pd.read_csv('Match.csv')
playerMatchesDF = pd.read_csv('Player_Match.csv')
playersDF = pd.read_csv('Player.csv')
seasonsDF = pd.read_csv('Season.csv')
teamsDF = pd.read_csv('Team.csv')


# In[3]:


def getMatchesForTeam(id):
    return matchesDF[(matchesDF["Team_Name_Id"] == id) | (matchesDF["Opponent_Team_Id"] == id)]


# In[4]:


def getMatchesWonByTeam(id):
    return matchesDF[matchesDF["Match_Winner_Id"] == id]


# In[5]:


def getTeamWinPercentage(id):
    result = 0
    totalMatches = len(getMatchesForTeam(id))
    matchesWon = len(getMatchesWonByTeam(id))
    if(totalMatches>0):
        result = (matchesWon*100)/totalMatches
    return result


# In[6]:


def getMatchesForTeamAgainstTeam(team_id,against_id):
    return matchesDF[((matchesDF["Team_Name_Id"] == team_id) & (matchesDF["Opponent_Team_Id"] == against_id)) | ((matchesDF["Team_Name_Id"] == against_id) & (matchesDF["Opponent_Team_Id"] == team_id))]


# In[7]:


def getMatchWonByTeamAgainstTeam(team_id,against_id):
    totalMatchesDF = getMatchesForTeamAgainstTeam(team_id,against_id)
    return totalMatchesDF[totalMatchesDF["Match_Winner_Id"] == team_id]


# In[8]:


def getMatchWonPercentageForTeamAgainstTeam(team_id,against_id):
    result = 0
    totalMatchesDF = getMatchesForTeamAgainstTeam(team_id,against_id)
    matchesWon = len(totalMatchesDF[totalMatchesDF["Match_Winner_Id"] == team_id])
    totalMatches = len(totalMatchesDF)
    if(totalMatches>0):
        result = (matchesWon*100)/totalMatches
    return result


# In[9]:


def getMatchWonPercentWhenTossWonForTeam(id):
    tossWonDF = matchesDF[matchesDF["Toss_Winner_Id"] == id]
    matchWonDF = tossWonDF[tossWonDF["Match_Winner_Id"] == id]
    return (len(matchWonDF)*100)/(len(tossWonDF))


# In[10]:


def getFirstBatWonPercentage(id):
    totalMatchesDF = getMatchesForTeam(id)
    batFirstMatchesDF = totalMatchesDF[((totalMatchesDF["Toss_Winner_Id"]==id) & (totalMatchesDF["Toss_Decision"] == 'bat')) | ((totalMatchesDF["Toss_Winner_Id"]!=id) & (totalMatchesDF["Toss_Decision"] == 'field'))]
    matchesWonDF = batFirstMatchesDF[batFirstMatchesDF["Match_Winner_Id"] == id]
    batFirstMatches = len(batFirstMatchesDF)
    if(batFirstMatches>0):
        matchesWon = len(matchesWonDF)
        return (matchesWon*100)/batFirstMatches
    return 0


# In[11]:


def geneareWinPercentageSheet():
    print("Generating WinPercent Data")
    data = pd.DataFrame( columns=('team_id','opponent_id','win_percentage'))
    pos = 0
    for index, row in teamsDF.iterrows():
        teamId = row["Team_Id"]
        for i, r in teamsDF.iterrows():
            ti = r["Team_Id"]
            if(ti != teamId):
                win_percent = np.nan
                matchesAgainst = len(getMatchesForTeamAgainstTeam(teamId,ti))
                matchesWonAgainst = len(getMatchWonByTeamAgainstTeam(teamId,ti))
                if(matchesAgainst > 0):
                    win_percent = (matchesWonAgainst*100)/matchesAgainst
                data.loc[pos,"team_id"] = teamId
                data.loc[pos,"opponent_id"] = ti
                data.loc[pos,"win_percentage"] = win_percent
                pos = pos + 1
    data.to_csv("../data/gen/win_percent.csv",sep=',')
    print("Done")


# In[12]:


def calculateBatsmanScore(row):
    PAR_AVG = 122.84
    score = 0
    runs = row["Runs"]
    fifties = row["Fifties"]
    hundreds = row["Hundreds"]
    bowlsPlayed = row["Bowls_Played"]
    out = row["Out"]
    average = 0
    if(bowlsPlayed>0):
        average = (runs*100)/bowlsPlayed
    wicketsAsFielder = row["Wickets_As_Fielder"]
    if(runs > 0):
        score = score + runs
        score = score + fifties*25
        score = score + hundreds*50
        if(out == 0):
            score = score + 10
        relative_avg = average/PAR_AVG
        score = score*relative_avg
    else:
        if(out == 1):
            score = score - 15
    if(wicketsAsFielder > 0):
        score = score + 10*wicketsAsFielder
    return score


# In[13]:


def calculateBowlerScore(row):
    score = 0
    wickets = row["Wickets"]
    runsConceded = row["Runs_Conceded"]
    economy = 0
    extras = row["Extras"]
    overs = row["Overs"]
    maidenOvers = row["Maiden_Overs"]
    wicketsAsFielder = row["Wickets_As_Fielder"]
    if(overs>0):
        economy = runsConceded/overs
    if(wickets > 0):
        score = score + 22.5*wickets
        if(wickets >= 4 ):
            score = score + 10*wickets
    if(extras >= 10):
        score = score - 10
    elif(extras >= 5):
        score = score - 5
    elif(extras > 0):
        score = score -2
    if(maidenOvers > 0):
        score = score + maidenOvers*10
    if(wicketsAsFielder > 0):
        score = score + 10*wicketsAsFielder
    return score


# In[14]:


def generatePlayerMatchScoreData():
    playersMatchesCompleteDF = pd.read_csv("../data/gen/player_match_complete.csv")
    playersMatchesCompleteDF = playersMatchesCompleteDF.convert_objects(convert_numeric=True)
    print("Generating PlayerMatchesComplete Data")
    data = pd.DataFrame(columns=('Match_Id','Player_Id','Team_Id','Is_Batsman','Is_Bowler','Is_Allrounder','Score'))
    pos = 0
    totalSize = len(playersMatchesCompleteDF)
    for index,row in playersMatchesCompleteDF.iterrows():
        print("Processing data...( %d %% done)" % int(pos*100/totalSize) )
        isBatsman = 0
        isBowler = 0
        isAllRounder = 0
        score = 0
        matchId = row["Match_Id"]
        playerId = row['Player_Id']
        teamId = row["Team_Id"]
        playerMatchesCompleteDF = playersMatchesCompleteDF[(playersMatchesCompleteDF["Player_Id"] == playerId)]
        totalMatches = len(playerMatchesCompleteDF)
        battedMatchedDF = playerMatchesCompleteDF[playerMatchesCompleteDF["Batted"] == 1]
        bowledMatchesDF = playerMatchesCompleteDF[playerMatchesCompleteDF["Bowled"] == 1]
        bothMatchesDF = playerMatchesCompleteDF[(playerMatchesCompleteDF["Batted"] == 1)&(playerMatchesCompleteDF["Bowled"] == 1)]
        battedMatches = len(battedMatchedDF)
        bowledMatches = len(bowledMatchesDF)
        bothMatches = len(bothMatchesDF)
        if(((bothMatches*100)/totalMatches) > 66):
            isAllRounder = 1
            isBatsman = 0
            isBowler = 0
            score = calculateBatsmanScore(row) + calculateBowlerScore(row)
        elif(battedMatches > bowledMatches):
            isBatsman = 1
            isAllRounder = 0
            isBowler = 0
            score = calculateBatsmanScore(row)
        else:
            isBowler = 1
            isBatsman = 0
            isAllRounder = 0
            score = calculateBowlerScore(row)
        data.loc[pos,'Match_Id'] = matchId
        data.loc[pos,'Player_Id'] = playerId
        data.loc[pos,"Team_Id"] = teamId
        data.loc[pos,'Is_Batsman'] = isBatsman
        data.loc[pos,'Is_Bowler'] = isBowler
        data.loc[pos,'Is_Allrounder'] = isAllRounder
        data.loc[pos,'Score'] = score
        pos = pos + 1
    data.to_csv("../data/gen/player_match_score.csv",sep=',')
    print("Done")


# In[15]:



def generatePlayerScoreData():
    print("Generating PlayerScore Data")
    data = pd.DataFrame(columns=('Player_Id','Player_Name','Total_Score','Avg_Score'))
    playersMatchesScoreDF = pd.read_csv("../data/gen/player_match_score.csv")
    pos = 0
    for index,row in playersDF.iterrows():
        score = 0
        totalScore = 0
        playerId = row["Player_Id"]
        name = row["Player_Name"]
        playerMatchesDF = playersMatchesScoreDF[playersMatchesScoreDF["Player_Id"] == playerId]
        totalMatches = len(playerMatchesDF)
        if(totalMatches>0):
            totalScore = playerMatchesDF["Score"].sum()
            score = totalScore/totalMatches
        data.loc[pos,"Player_Id"] = playerId
        data.loc[pos,"Player_Name"] = name
        data.loc[pos,"Total_Score"] = totalScore
        data.loc[pos,"Avg_Score"] = score
        pos = pos + 1
    data.to_csv("../data/gen/player_score.csv",sep=',')
    print("Done")


# In[ ]:




