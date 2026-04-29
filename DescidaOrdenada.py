from matplotlib import pyplot as plt
import numpy as np
import random
import math
import floris.tools.visualization as wakeviz
from floris.tools import FlorisInterface, WindRose
from windrose import WindroseAxes
from floris.tools.layout_functions import visualize_layout
import pandas as pd
from datetime import datetime



import os
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
fi = FlorisInterface("inputs/gch.yaml") # Criando a Interface Floris com valores iniciais importados do arquivo gch.yaml
wind_rose = WindRose()



# ==================================================================================================================================
# Parâmetros do algoritmo genético

COUNT = 10              # Número de repetições de gerações consecutivas para valores de aptidão iguais (CRITÉRIO DE PARADA)
TAXA_MUTACAO=0.2
r0=40.0                 # Raio da turbina
D=2*r0

tabelaDescidaOrdenada = []

x = np.array([0, 560, 1120, 1680, 2240, 2800, 3360, 3920, 4480, 5040])
y = np.array([0, 560, 1120, 1680, 2240, 2800, 3360, 3920])

X, Y = np.meshgrid(x, y)

coords_x = X.flatten()
coords_y = Y.flatten()

#layout_y=[0, 0, 0, 0, 400, 400, 400, 400]                 # Layout das coordenadas do eixo X
#layout_x=[0., 100., 200., 300, 0., 100., 200., 300]          # Layout das coordenadas do eixo Y

layout_y=coords_y
layout_x=coords_x

wind_directions = [90]
wind_speeds = [11]
        
NUM_TURBINAS = len(layout_x)        # Número de turbinas no parque eólico

# True = Sim ---- False = Não
plotarWake = False                  # Plotar Efeito de Esteira
plotarLayout = False                # Plotar Layout do parque
plotarPotencia = False               # Plotar Histórico de Potência
plotarPotIndividual = False          # Plotar Potências das turbinas individuais
printOtimizacao = True              # Print dos valores de potência/ângulos ótimos
# ==================================================================================================================================

## ================================== Subrotina de calculo de produção total do parque =====================================

def calculo_producao_sem_otimizacao(ws, wd, fi, i):
    vetor_zerado = np.zeros(NUM_TURBINAS)

    u_points = fi.floris.flow_field.u
    fi.calculate_wake()
    
            

    fi.reinitialize(wind_speeds=[ws[i]], wind_directions=[wd[i]])  # Passando a velocidade e direção do vento atual para o FlorisInterface
  
        # Configurando os ângulos de inclinação para todas as turbinas
    for j in range(len(vetor_zerado)):
        yaw_angles[0,0,j] = vetor_zerado[j]
            
        fi.calculate_wake(yaw_angles=yaw_angles)
        farm_power = fi.get_farm_power()
    producao_total = np.sum(farm_power/1e3)
    return producao_total


def calculo_producao_total(num_turbinas, individuo, ws, wd, fi, i):

    u_points = fi.floris.flow_field.u
    fi.calculate_wake()
    
            
    fi.reinitialize(wind_speeds=[ws[i]], wind_directions=[wd[i]])  # Passando a velocidade e direção do vento atual para o FlorisInterface
  
        # Configurando os ângulos de inclinação para todas as turbinas
    for j in range(len(individuo)):
        yaw_angles[0,0,j] = individuo[j]
            
        fi.calculate_wake(yaw_angles=yaw_angles)
        farm_power = fi.get_farm_power()
    producao_total = np.sum(farm_power/1e3)
    return producao_total


## ============================================ =============================================================================
def descida_ordenada(individuo):
    melhorou = True
    producao_atual=0
    producao_teste=0
    teste_mutacao=0
    angulo_mutacao=0

    while melhorou:
        melhorou = False
        yaw_angles[0,0,:] = individuo
        producao_atual = calculo_producao_total(num_turbine, yaw_angles[0,0,:], wind_speeds, wind_directions, fi, 0)
        print(f"Indivíduo: [{individuo}], Fitness = {producao_atual:.2f} kW - Produção Inicial")
        
        # percorre do último ao primeiro
        for i in reversed(range(len(layout_x))):
     
            while True:
                
                teste_mutacao=random.random()
                #print(teste_mutacao)
                if individuo[i] < 30 and teste_mutacao>TAXA_MUTACAO:
                    individuo[i] += 1
                    yaw_angles[0,0,:] = individuo
                    producao_teste = calculo_producao_total(num_turbine, yaw_angles[0,0,:], wind_speeds, wind_directions, fi, 0)
                    if producao_teste > producao_atual:
                        melhorou = True
                        print(f"Indivíduo: [{individuo}], Fitness = {producao_teste:.2f} kW")
                        producao_atual=producao_teste
                        continue
                    else:
                        print(f"Indivíduo: [{individuo}], Fitness = {producao_teste:.2f} kW - Diminuiu - Descartado")
                        individuo[i] -= 1  # desfaz
                        
                # Teste: Negativo
                if individuo[i] > -30 and teste_mutacao>TAXA_MUTACAO:
                    individuo[i] -= 1
                    yaw_angles[0,0,:] = individuo
                    producao_teste = calculo_producao_total(num_turbine, yaw_angles[0,0,:], wind_speeds, wind_directions, fi, 0)
                    if producao_teste > producao_atual:
                        melhorou = True
                        print(f"Indivíduo: [{individuo}], Fitness = {producao_teste:.2f} kW")
                        producao_atual=producao_teste
                        # print("Teste :", producao_teste)
                        # print("Atual :", producao_atual)
                        continue
                    else:
                        print(f"Indivíduo: [{individuo}], Fitness = {producao_teste:.2f} kW - Diminuiu - Descartado")
                        individuo[i] += 1  # desfaz
                  
                  
                if teste_mutacao < TAXA_MUTACAO:
                    angulo_mutacao = int(random.uniform(-30, 30))
                    posicao_alterada = int(random.uniform(0, len(layout_x)))
                    individuo_anterior=individuo[posicao_alterada]
                    individuo[posicao_alterada]=angulo_mutacao
                    yaw_angles[0,0,:] = individuo

                    producao_teste = calculo_producao_total(num_turbine, yaw_angles[0,0,:], wind_speeds, wind_directions, fi, 0)
                    if producao_teste>producao_atual:
                        melhorou = True
                        print(f"Indivíduo: [{individuo}], Fitness = {producao_teste:.2f} kW (Aleatório)")
                        # print("Teste :", producao_teste)
                        # print("Atual :", producao_atual)
                        producao_atual=producao_teste                       
                        continue
                    else:
                        print(f"Indivíduo: [{individuo}], Fitness = {producao_teste:.2f} kW - Diminuiu - Descartado (Aleatório)")
                        individuo[posicao_alterada] = individuo_anterior  # desfaz  
                        continue
                        
                            
                break

               
            
                

    return individuo


## ============================================ PARÂMETROS DE SIMULAÇÃO ===========================================

fi.reinitialize(layout_x=layout_x, layout_y=layout_y)  # Layout do parque
turbine_name = []  # Lista para armazenar os nomes das turbinas

for i in range(len(fi.layout_x)):       # Laço para nomear as turbinas no formato 'T01' usando o length do layout
    turbine_name.append('T{:02d}'.format(i+1))
    
D = 126.0 # Diâmetro do rotor NREL 5 MW
fi.reinitialize(wind_directions=wind_directions)
num_wd = len(wind_directions)  # Quantidade de posições do vetor: Wind Directions
num_ws = len(wind_speeds)  # Quantidade de posições do vetor: Wind 
num_turbine = len(fi.layout_x)  # Quantidade de turbinas no parque eólico
yaw_angles = np.zeros((1, 1, num_turbine))
melhor_yaw_historico = np.zeros((1, len(wind_speeds), num_turbine))

TAMANHO=11
Passo=5
potencia = np.zeros((TAMANHO, len(wind_speeds)))
populacao = []

indices = [0] * NUM_TURBINAS
producao_anterior=0
producao_atual=0

angulo = 0


individuo = np.zeros(80)
melhor_individuo=descida_ordenada(individuo)
yaw_angles[0,0,:] = melhor_individuo
melhor_producao=producao_total=calculo_producao_total(num_turbine, yaw_angles[0,0,:], wind_speeds, wind_directions, fi, 0)
print("Melhor individuo: ", melhor_individuo, " -- Melhor produção: ", melhor_producao)

                
                       
# Cria tabelaDescidaOrdenada
df = pd.DataFrame(tabelaDescidaOrdenada, columns=[
    "T1", "T2", "T3", "T4", "Producao"
])
# Exporta para Excel
df.to_excel("tabelaDescidaOrdenada.xlsx", index=False)
         

        
    
print()
print()
