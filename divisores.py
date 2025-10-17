#Declarando o vetor
numeros = []

#Função que lê os números inseridos pelo usuário e valida se são maiores que 1 
# ou se já estão inseridos no vetor, e encerra quando o inserido for '-1'
def ler_numeros(lista_numeros):
    while True: #enquanto essa condição for verdadeira
        escolha = int(input("insira numero: ")) #Leitura da escolha e 
                                                #conversão do input para inteiro
        if escolha > 1 and escolha not in numeros: #validação
            numeros.append(escolha) #adicionar o valor no vetor numeros 
            
        if escolha == -1: #valida SE a regra do while ainda esta sendo respeitada e para 
            break


#Execução da primeira função
ler_numeros(numeros)


#Função que encontra os divisores dos números inseridos no primeiro vetor e 
# adiciona no segundo vetor, e que depois os exibem
def encontra_divisores(lista_numeros):
    for numero in lista_numeros: #for para cada elemento fazemos tal coisa
        divisores = [] #lista 
        for i in range(1, numero + 1): #laço 'for' com controlador (i) que controla a repetição do bloco 
                                       #e condição de repetição
            if numero % i == 0 and i > 1 and i != numero: #valida se i é divisor do numero sobrando 0
                                                          # e se é maior que 1 ou ele mesmo e vai entrar na lista de div
                divisores.append(i)
        
        if(len(divisores) == 0):          #se o numero nao entra nas regras do if anterior, ele entra "de fora" só 
            divisores.extend([1, numero]) # podendo ser primo ou seja 1 e ele mesmo 
        
        print(f"O número {numero} tem como divisores os numeros {divisores[0]} e {divisores[-1]} ")


#Execução do segundo vetor
encontra_divisores(numeros)
