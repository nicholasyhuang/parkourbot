from __future__ import division
import numpy as np

import MalmoPython
import os
import random
import sys
import time
import json
import random
import math
import errno

def getPlatformsDrawing(positions):
    drawing = ""
    for p in positions:
        drawing += '<DrawBlock x="' + str(p[0]) + '" y="' + str(int(p[1])+226) + '" z="' + str(int(p[2])) + '" type="diamond_block" />\n'
    return drawing

def parsePositionsFile(path):
    '''Parses file from path into list
       Format: [x1, y1, z1]
               [x2, y2, z2]
               [x3, y3, z3]'''
    try:
        with open(path, 'r') as file:
            lines = file.readlines()
            file.close()
    except FileNotFoundError:
        print(f"Error: File at {path} not found.")
        return None
    
    coordinates = []
    for line in lines:
        coord = []
        for partialCoord in line.split(" "):
            coord.append(partialCoord.strip())
        if len(coord) != 3:
            raise SyntaxError("File not formatted correctly")
        coordinates.append(coord)
    return coordinates

def BuildXML(path):
    #TODO make the final jump platform the goal
    '''Takes path to blocks file and builds XML mission with it'''
    summary = "Mission from file at " + path

    positions = parsePositionsFile(path)

    namedPointXML = ''
    for i, position in enumerate(positions):
        namedPointXML += '<Marker name="platform' + str(i) + '" x="' + str(position[0]) + '" y="' + str(int(position[1])+227) + '" z="' + str(int(position[2])) + '"/>\n'

    endGoal = positions[-1]
    endGoalXML = '<Marker x="' + str(int(endGoal[0])+0.5) + '" y="' + str(int(endGoal[1])+227) + '" z="' + str(int(endGoal[2])+0.5) + '" tolerance="0.5" description="Goal_found"/>'

    XML = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <About>
            <Summary>''' + summary + '''</Summary>
        </About>

        <ModSettings>
            <MsPerTick>50</MsPerTick>
        </ModSettings>

        <ServerSection>
            <ServerInitialConditions>
                <Time>
                    <StartTime>6000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                </Time>
                <Weather>clear</Weather>
                <AllowSpawning>false</AllowSpawning>
            </ServerInitialConditions>
            <ServerHandlers>
                <FlatWorldGenerator generatorString="3;7,220*1,5*3,2;3;,biome_1" />
                <DrawingDecorator>
                    <DrawCuboid x1="-50" y1="226" z1="-50" x2="50" y2="228" z2="50" type="air" />
                    <DrawCuboid x1="-50" y1="226" z1="-50" x2="50" y2="226" z2="50" type="monster_egg" variant="chiseled_brick" />
                    <DrawCuboid x1="-50" y1="226" z1="-50" x2="50" y2="226" z2="50" type="lava" />
                    <DrawBlock x="-0" y="226" z="0" type="diamond_block"/>
                    ''' + getPlatformsDrawing(positions) + '''
                </DrawingDecorator>
                <ServerQuitFromTimeUp timeLimitMs="10000"/>
            </ServerHandlers>
        </ServerSection>

        <AgentSection mode="Survival">
            <Name>test</Name>

            <AgentStart>
                <Placement x="0.5" y="227.0" z="0.5"/>
            </AgentStart>
            <AgentHandlers>
                <ObservationFromFullStats/>
                <ObservationFromDistance>
                    ''' + namedPointXML + '''
                </ObservationFromDistance>
                <ContinuousMovementCommands turnSpeedDegs="180"/>
                <HumanLevelCommands/>
                <MissionQuitCommands/>
                <AgentQuitFromReachingPosition>
                    ''' + endGoalXML + '''
                </AgentQuitFromReachingPosition>
            </AgentHandlers>
        </AgentSection>
    </Mission>'''
    
    return XML


 

if(__name__=='__main__'):
    print('Starting...', flush=True)

    agent_host = MalmoPython.AgentHost()
    try:
        agent_host.parse(sys.argv)
    except RuntimeError as e:
        print('ERROR:', e)
        print(agent_host.getUsage())
        exit(1)
    if agent_host.receivedArgument("help"):
        print(agent_host.getUsage())
        exit(0)
    
    print(BuildXML("test.txt"))

    my_mission = MalmoPython.MissionSpec(BuildXML("test.txt"), True)
    my_mission_record = MalmoPython.MissionRecordSpec()

    max_retries = 3
    for retry in range(max_retries):
        try:
            agent_host.startMission(my_mission, my_mission_record)
            break
        except RuntimeError as e:
            if retry == max_retries -1:
                print("Error starting mission:", e)
                exit(1)
            else:
                time.sleep(2)
    
    print("Waiting for mission to start ", end=" ")
    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        print(".", end="")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:", error.text)
    
    print()
    print("Mission running ", end=' ')


    agent_host.sendCommand("turn 1")
    #agent_host.sendCommand("sprint 1")
    #agent_host.sendCommand("move 1")
    time.sleep(1)
    agent_host.sendCommand("sprint 1")
    agent_host.sendCommand("move 1")
    time.sleep(0.1)
    agent_host.sendCommand("jump 1")



    while world_state.is_mission_running:
        print(".", end="")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()

        #GETTING DEATH POSITION
        if(len(world_state.observations) > 0):
            print(world_state.observations[-1].text)
            msg = world_state.observations[-1].text
            ob = json.loads(msg)
            if(ob["TimeAlive"]==0):
                x = ob["XPos"]
                y = ob["YPos"]
                z = ob["ZPos"]
                print("Died at", x, y, z)
                agent_host.sendCommand("quit")
        else:
            agent_host.sendCommand("quit")

        for error in world_state.errors:
            print("Error:", error.text)

    print()
    print("Mission ended")

