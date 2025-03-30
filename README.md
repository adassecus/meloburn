## Visão Geral

- **Organização de Músicas:** Separa os arquivos musicais por artista e álbum.
- **Renomeação e Numeração de Faixas:** Corrige os metadados e padroniza os nomes dos arquivos, facilitando a navegação em aparelhos de som.
- **Otimização para Pen Drives:** Oferece duas opções de operação:
  - **Formatar o pen drive:** Apaga todo o conteúdo antes de copiar as músicas.
  - **Adicionar músicas:** Copia novas músicas sem apagar o conteúdo já existente.
- **Exibição de Progresso Detalhado:** Acompanha todo o processo com barra de progresso interativa.
- **Busca de Metadados Online:** Utiliza múltiplas APIs (Last.fm, MusicBrainz, Discogs, TheAudioDB) para identificar e corrigir automaticamente artistas, álbuns e títulos.

---

## Funcionalidades

- **Interface Gráfica com Tkinter:** Simples, intuitiva e elegante com design moderno.
- **Verificação de Privilégios Administrativos:** Garante que o script seja executado com as permissões necessárias para operações de sistema, como a formatação do pen drive.
- **Fluxo de Trabalho Guiado:** Interface passo a passo que orienta o usuário durante todo o processo.
- **Busca de Metadados Integrada:** Combina múltiplas fontes para enriquecer seus arquivos de música:
  - Last.fm: Para informações detalhadas sobre artistas e músicas
  - MusicBrainz: Para metadados precisos de álbuns e faixas
  - Discogs: Para capas de álbum e informações adicionais
  - TheAudioDB: Como fonte adicional de informações
- **Download de Capas de Álbum:** Busca e baixa automaticamente capas de álbum para cada pasta organizada.
- **Detecção de Idioma:** Identifica o idioma das músicas para melhor organização.
- **Monitoramento do Progresso:** Barra de progresso detalhada durante o processamento e cópia dos arquivos.
- **Renomeação de Pen Drive:** Permite definir um nome personalizado para o dispositivo.

---

## Opções de Instalação

### Opção 1: Versão Executável (Recomendada)

Não requer Python nem instalação de dependências! Basta baixar e executar.

1. **Baixe o arquivo executável**:
   - Faça o download do arquivo `meloburnwin.exe` deste repositório
   - Salve-o em qualquer pasta do seu computador

2. **Execute o programa**:
   - Clique duas vezes no arquivo `meloburnwin.exe` para iniciar o programa
   - Ao ser solicitado, permita a execução como administrador para as operações de formatação de pen drive

Essa versão executável contém todas as dependências necessárias e funciona em qualquer sistema Windows sem configuração adicional.

### Opção 2: Versão Python (Para desenvolvedores)

#### Requisitos

- **Python 3.x** – [Download Python](https://www.python.org/downloads/)
- **Tkinter:** Geralmente incluído com o Python em ambientes Windows.
- **Mutagen:** Para manipulação de metadados de arquivos de áudio.  
  ```bash
  pip install mutagen
  ```
- **Requests:** Para realizar requisições às APIs de metadados.  
  ```bash
  pip install requests
  ```

#### Instalação e Configuração

1. **Obtenha o código-fonte**:
   - Baixe o arquivo `meloburnwin.py` deste repositório

2. **(Opcional) Crie um Ambiente Virtual**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instale as Dependências**:
   ```bash
   pip install mutagen requests
   ```

4. **Execute o Script**:
   ```bash
   python meloburnwin.py
   ```

### Chaves de API (Opcional)

O programa já vem com chaves de API padrão configuradas para:
- Last.fm
- Discogs
- MusicBrainz

Se você quiser usar suas próprias chaves, você pode editar o código-fonte e substituir os valores no dicionário `API_KEYS` no início do arquivo.

---

## Como Utilizar

### Navegação pela Interface

1. **Tela de Boas-vindas:** 
   - Clique em "Iniciar" para começar o processo

2. **Etapa 1 - Selecione a Pasta de Origem:** 
   - Escolha a pasta que contém seus arquivos de música
   - O programa analisará recursivamente todas as subpastas

3. **Etapa 2 - Selecione o Pen Drive:** 
   - Escolha o dispositivo onde as músicas serão organizadas
   - Tenha cuidado ao selecionar o destino correto

4. **Etapa 3 - Configurações:** 
   - Escolha o modo de operação:
     - **Formatar o pen drive:** Apaga todo conteúdo existente
     - **Adicionar músicas:** Mantém o conteúdo existente
   - Defina um nome personalizado para o dispositivo

5. **Resumo da Operação:** 
   - Verifique todas as opções selecionadas
   - Clique em "Iniciar Processo" para começar

6. **Durante o Processo:**
   - Acompanhe o progresso pela barra de progresso
   - Visualize detalhes sobre a etapa atual
   - Você pode cancelar a operação a qualquer momento

### Executando com Privilégios Administrativos

Para garantir o funcionamento completo (especialmente para formatação de dispositivos):

1. **Usando o Executável (.exe):**
   - Clique com o botão direito em `meloburnwin.exe`
   - Selecione "Executar como administrador"

2. **Usando a Versão Python:**
   - Execute o Prompt de Comando como administrador
   - Navegue até a pasta do script
   - Execute: `python meloburnwin.py`

3. **Criando um Atalho com Privilégios:**
   - Clique com o botão direito no arquivo (exe ou py)
   - Selecione "Criar atalho"
   - Clique com o botão direito no atalho criado e escolha "Propriedades"
   - Na aba "Compatibilidade", marque "Executar este programa como administrador"
   - Clique em "OK" para salvar

---

## Recursos Técnicos Adicionais

- **Cache de Metadados:** O programa salva um cache de pesquisas anteriores para melhorar o desempenho.
- **Processamento Multi-fonte:** Combina dados de várias APIs para resultados mais precisos.
- **Detecção de Idioma:** Algoritmo básico para identificar o idioma com base em palavras comuns.
- **Sanitização de Nomes de Arquivo:** Garante nomes de arquivo compatíveis com sistemas de arquivos.
- **Manipulação de Vários Formatos:** Suporta MP3, FLAC, WAV, AAC, OGG, M4A e WMA.

---

## Contato

Para dúvidas, sugestões ou problemas, entre em contato:

📩 **[t.me/adassecus](https://t.me/adassecus)**
