import json
import os
import sqlite3
import hashlib

def hash_password(password)
    Gera um hash SHA256 para a senha.
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_db_connection()
    Cria e retorna uma conexão com o banco de dados.
    # O script está em scripts, o DB está na raiz (..)
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_data(conn)
    Busca todos os dados do banco de dados.
    products = conn.execute('SELECT  FROM products').fetchall()
    users = conn.execute('SELECT  FROM users').fetchall()
    vendas_log = conn.execute('SELECT  FROM vendas_log').fetchall()
    
    # Converte os dados para dicionários
    products_list = [dict(row) for row in products]
    users_list = [dict(row) for row in users]
    vendas_log_list = [dict(row) for row in vendas_log]
    
    return products_list, users_list, vendas_log_list

def apply_changes(conn, changes)
    Aplica as alterações recebidas ao banco de dados.
    cursor = conn.cursor()
    
    for change in changes
        action = change.get('action')
        details = change.get('details')
        
        if action == 'create_product'
            cursor.execute(
                'INSERT INTO products (cod, name, price, barcode, category, subcategory, subsubcategory, estoque, prc_total) VALUES (, , , , , , , , )',
                (details['cod'], details['name'], details.get('price', 0), details.get('barcode'), details.get('category'), details.get('subcategory'), details.get('subsubcategory'), details.get('estoque'), details.get('prc_total'))
            )
        elif action == 'pair_product'
            cursor.execute(
                'UPDATE products SET barcode = , estoque =  WHERE cod = ',
                (details['newBarcode'], details.get('newStock'), details['cod'])
            )
        elif action == 'adjust_stock'
            cursor.execute(
                'UPDATE products SET estoque =  WHERE cod = ',
                (details['newStock'], details['cod'])
            )
        elif action == 'create_user'
            cursor.execute(
                'INSERT INTO users (username, password, role) VALUES (, , )',
                (details['username'], details['password'], details['role'])
            )
        # Adicione outras ações conforme necessário
            
    conn.commit()

def apply_sales(conn, sales)
    Insere novos registros de vendas no banco de dados.
    cursor = conn.cursor()
    for sale in sales
        cursor.execute(
            'INSERT INTO vendas_log (timestamp, vendedor, produtos, formas_pagamento, valores_pagos, desconto, valor_total) VALUES (, , , , , , )',
            (sale['timestamp'], sale['vendedor'], sale['produtos'], sale['formas_pagamento'], sale['valores_pagos'], sale['desconto'], sale['valor_total'])
        )
    conn.commit()

def main()
    Função principal do script.
    changes_json = os.environ.get('CHANGES_JSON')
    if not changes_json
        print(Nenhuma alteração recebida. Apenas gerando o arquivo JSON.)
        changes_to_apply = []
        sales_to_apply = []
    else
        try
            data = json.loads(changes_json)
            changes_to_apply = data.get('changes', [])
            sales_to_apply = data.get('sales', [])
        except json.JSONDecodeError
            print(Erro ao decodificar o JSON de alterações.)
            return

    conn = get_db_connection()
    
    # Aplica as alterações se houver alguma
    if changes_to_apply
        print(fAplicando {len(changes_to_apply)} alterações ao banco de dados...)
        apply_changes(conn, changes_to_apply)

    # Aplica as vendas se houver alguma
    if sales_to_apply
        print(fAdicionando {len(sales_to_apply)} novos registros de vendas...)
        apply_sales(conn, sales_to_apply)

    # Busca todos os dados atualizados
    products, users, vendas_log = get_all_data(conn)
    
    # Define a versão (pode ser aprimorado)
    # Lendo a versão atual e incrementando
    json_output_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'dados_offline.json')
    version = 1.0.0.0.0.1
    try
        with open(json_output_path, 'r', encoding='utf-8') as f
            current_data = json.load(f)
            version_parts = current_data.get('version', '1.0.0.0.0.0').split('.')
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            version = ..join(version_parts)
    except (FileNotFoundError, json.JSONDecodeError)
        pass # Usa a versão padrão se o arquivo não existir ou for inválido

    # Cria o dicionário final para o JSON
    output_data = {
        version version,
        products products,
        users users,
        vendas_log vendas_log
    }
    
    # Salva o arquivo JSON
    with open(json_output_path, 'w', encoding='utf-8') as f
        json.dump(output_data, f, ensure_ascii=False, indent=4)
        
    print(fArquivo 'dados_offline.json' atualizado com sucesso para a versão {version} em {json_output_path})

    conn.close()

if __name__ == '__main__'
    main()
