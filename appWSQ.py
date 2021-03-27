from flask import Flask, request, Blueprint, abort
from flask_restx import Api, Resource, fields, reqparse
from flask_cors import CORS

import json, configparser
from io import BytesIO
import wsq
import base64
import PIL.Image

from PIL import Image, ImageEnhance, ImageDraw
import cx_Oracle
import pathlib
from werkzeug.datastructures import FileStorage
import cv2

app = Flask(__name__)
CORS(app)

blueprint = Blueprint('api', __name__)

api = Api(blueprint, 
            doc='/doc' ,
            version='v1',
            title='Conversor WSQ em base64(PNG)', description='Sistema para conversão de digitais em formato WSQ para formato de imagem',
            default="Solicitação",
            default_label="Solicitação de conversão de WSQ"
            )

app.config['JSON_AS_ASCII'] = False
app.register_blueprint(blueprint)

user = None
senha = None
endereco_bd = None

#db_pool = cx_Oracle.SessionPool(user, senha, endereco_bd, min = 1, max = 3, increment = 1, threaded = True, encoding="UTF-8",nencoding='UTF-8')

dedos = api.model('dedos',{
                  'nrDedo':fields.Integer(required=True, description='nr do dedo'),
                  'dedo_impresso': fields.String(skip_none=True),
                  'digital' : fields.String(skip_none=True)})
digital = api.model('digitais',{'digitais': 
                           fields.Nested(dedos,allow_null = True,skip_none=True)})
dedo = api.model('dedos',{
                  'nrDedo':fields.Integer(required=True, description='nr do dedo'),
                  'digital' : fields.String(skip_none=True)})
digitalImpressa = api.model('digitais',{'digitais': 
                            fields.Nested(dedo,allow_null = True,skip_none=True)})

image = api.model('imagem',{
                        'img':fields.String(required=True, description='imagem codificada em base64')
})

@api.route('/listaDigitaisCPF/<cpf>')
@api.param('cpf', 'numero do pedido')
@api.doc( description="Função que busca as digitais no banco de dados e converte em PNG")
class WSQPedido(Resource):
    @api.marshal_with(dedos, as_list=True, skip_none=True,mask=False)
    def get(self, cpf):
        if not cpf:
            return('Não é possivel buscar as digitais sem o CPF.',400)
            
        connection = db_pool.acquire()
        cursor = connection.cursor()
        query = "SELECT DI_DIGITAL, NRDEDO, DEDO_IMPRESSO FROM  DIGITAL WHERE CPF = :nr_cpf"
        try:
            cursor.execute(query,{'nr_cpf': cpf})
            result=cursor.fetchall()
            if not result:
                return ('Nenhuma digital com o CPF informado.',404)

            saida = [dict(zip([key[0] for key in cursor.description], row)) for row in result]

            dedos =[]
            for dedo in saida:
                try:
                    bdigi= dedo['DI_DIGITAL'].read()

                    dedo_decode = converterWSQtoPNG(str(base64.b64encode(bdigi).decode("utf-8")),1)
                    dedos.append({'nrDedo':dedo['NRDEDO'],'dedo_impresso':dedo['DEDO_IMPRESSO'],'digital':dedo_decode})

                except AttributeError as e:
                    dedos.append({'nrDedo':dedo['NRDEDO'],'dedo_impresso':dedo['DEDO_IMPRESSO']})
            
            return dedos,200
        except Exception as e:
            abort(400, 'Erro ao buscar dados, campo: {}'.format(e))
        finally:
            cursor.close()
            db_pool.release(connection)

@api.route('/converterWSQ')
@api.doc( description="Função que converte base64(WSQ) em PNG")
class converterWSQ(Resource):
    @api.expect(image, validate=True)
    def post(self):
        '''Recebe uma digital em WSQ encodado em base64 e converte em PNG'''
        if request.method == "POST":
            data = json.loads(request.data) 

        return {"img": converterWSQtoPNG(data['img'],1)}

@api.route('/converterWSQlist', methods=["POST"])
@api.doc( description="Função que recebe uma lista de WSQ em base64 e converte em PNG")
class converterWSQlist(Resource):
    @api.expect([image], validate=True)
    def post(self):
        '''Recebe uma lista de WSQbase64 e converte em PNG'''
        if request.method == "POST":
            data = json.loads(request.data)

        digitais = []
        for dedos in data:
            digConvertido = converterWSQtoPNG(data[dedos],1)
            digitais.update( {dedos: digConvertido} )  
        with open('textoBase64.txt', 'w') as arquivo:
                print(digitais, file=arquivo)
        return (json.dumps(digitais))


@api.route('/converterWSQ90', methods=["POST"])
@api.doc( description="Função que recebe uma WSQ em base64, rotaciona 90º e converte em PNG")
class converterWSQ90(Resource):
    @api.expect(image, validate=True)
    def post(self):
        '''Recebe uma digital em WSQbase64, converte em PNG girando em 90° a imagem'''
        if request.method == "POST":
            data = json.loads(request.data)
            
        return {"img": converterWSQtoPNG90(data['img'],1)} 


@api.route('/removeFundo', methods=["POST"])
@api.doc( description="Função que remove o fundo de imagem. Ajustado para remover fundo de digital e assinatura")
class removeFundo(Resource):
    @api.expect(image, validate=True)
    def post(self):
        '''recebe uma assinatura ou digital e remove o fundo'''
        if request.method == "POST":
            data = json.loads(request.data)
            
        #return removerFundo(data['img'],1)
        return removeFundo2(data['img'])


upload_parser = api.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)

@api.route('/upload/<extensao>')
@api.param('extensao', 'extensao do arquivo de retorno (JPEG, PNG, WSQ)')
@api.doc( description="Carrega um arquivo e transforma em base64")
@api.expect(upload_parser)
class Upload(Resource):
    def post(self, extensao):
        #if ternario
        extensao = extensao.upper()

        file = request.files['file']
        #abre com o Pillow
        im = PIL.Image.open(file)
        #gera um buffer (espaço em memoria)
        buffered = BytesIO()
        #salva no buffer a imagem lida no formato
        im.save(buffered, format='JPEG')
        #trasnforma o buffer em base64
        img_str = base64.b64encode(buffered.getvalue())
        #remove b (byte da string)
        base64_bytes = img_str.decode('utf-8')
        if (extensao == 'PNG' or extensao == 'JPEG'):
            return 'data:image/jpeg;base64,'+base64_bytes, 200
        else:
            return base64_bytes, 200

def converterWSQtoPNG(digital, tipo):
    #decodifica a imagem e abre com o Pillow
    im = PIL.Image.open(BytesIO(base64.b64decode(digital)))
    #gera um buffer (espaço em memoria)
    buffered = BytesIO()
    #salva no buffer a imagem lida no formato PNG
    im.save(buffered, format="PNG")
    #trasnforma o buffer em base64
    img_str = base64.b64encode(buffered.getvalue())
    #remove b (byte da string)
    base64_bytes = img_str.decode('utf-8')

    if(tipo == 1):
        return base64_bytes
    elif(tipo == 2):
        #pego diretorio atual
        diretorio = pathlib.Path()
        #listo os arquivos.png
        arquivos = diretorio.glob('*.png')
        maiorNr = 0
        for arquivo in arquivos:
            #pego os valores antes de .png e somo +1
            nr = str(arquivo)[:-4]
            maiorNr = int(max(nr, key=int))+1
        #im = PIL.Image.open(BytesIO(base64.b64decode(digital)))
        im.save("{}.png".format(str(maiorNr)))
    else:
        with open('textoBase64.txt', 'w') as arquivo:
            print("data:image/png;base64,{}".format(base64_bytes), file=arquivo)


def converterWSQtoPNG90(digital,tipo):

    #decodifica a imagem e abre com o Pillow
    im = PIL.Image.open(BytesIO(base64.b64decode(digital)))
    #gera um buffer (espaço em memoria)
    buffered = BytesIO()
    #rotaciona a imagem em 90 grau
    rotated_image = im.rotate( 90, expand=1 )
    #salva no buffer a imagem lida no formato PNG
    rotated_image.save(buffered, format="PNG")
    #trasnforma o buffer em base64
    img_str = base64.b64encode(buffered.getvalue())
    if(tipo == 1):
        return img_str
    else:
        #base64_bytes = img_str.encode('UTF-8')
        with open('nomeDoArquivo.txt', 'w') as arquivo:
            print("data:image/png;base64,{}".format(img_str), file=arquivo)

def removerFundo(image, tipo):
    #decodifica a imagem e abre com o Pillow
    img = PIL.Image.open(BytesIO(base64.b64decode(image)))
    #gera um buffer (espaço em memoria)
    buffered = BytesIO()

    enhancer = PIL.ImageEnhance.Contrast(img)
    #para fotografia 2, digital 5, assin 5)
    enhanced_im = enhancer.enhance(5.0)
    img = enhanced_im.convert("RGBA")
    datas = img.getdata()

    newData = []
    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            newData.append((255, 255, 255, 0))

        else:
            newData.append(item)

    img.putdata(newData)

    #salva no buffer a imagem lida no formato PNG
    img.save(buffered, format="PNG")
    #trasnforma o buffer em base64
    img_str = base64.b64encode(buffered.getvalue())
    #remove b (byte da string)
    base64_bytes = img_str.decode('utf-8')
    #aqui pode retornar o base64_bytes
    if(tipo == 1):
        return "data:image/png;base64,"+base64_bytes
    else:
        #reconverto o base64 em byte
        im = PIL.Image.open(BytesIO(base64.b64decode(base64_bytes)))
        #pego diretorio atual
        diretorio = pathlib.Path()
        #listo os arquivos.png
        arquivos = diretorio.glob('*.png')
        #salvar em png
        im.save("image.png")
        return "{msg: Ok}",200


if __name__ == "__main__":
    app.run(host='0.0.0.0',port='8080', debug=False)

