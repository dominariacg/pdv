import json
import os
import sqlite3
import hashlib

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_data(conn):
    """Busca todos os dados do banco de dados para gerar o JSON final."""
    products = [dict(row) for row in conn.execute('SELECT * FROM products').fetchall()]
    users = [dict(row) for row in conn.execute('SELECT * FROM users').fetchall()]
    vendas_log = [dict(row) for row in conn.execute('SELECT * FROM vendas_log').fetchall()]
    return products, users, vendas_log

def apply_changes_incrementally(conn, changes):
    """
    Aplica as alterações de forma inteligente, verificando a existência
    dos registros antes de inserir, atualizar ou excluir.
    """
    cursor = conn.cursor()
    
    for change in changes:
        action = change.get('action')
        details = change.get('details')
        
        try:
            if action == 'create_product':
                cursor.execute("SELECT cod FROM products WHERE cod = ?", (details['cod'],))
                if cursor.fetchone() is None:
                    cursor.execute(
                        'INSERT INTO products (cod, name, price, barcode, category, subcategory, subsubcategory, estoque, prc_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (details['cod'], details.get('name'), details.get('price', 0), details.get('barcode'), details.get('category'), details.get('subcategory'), details.get('subsubcategory'), details.get('estoque'), details.get('prc_total'))
                    )
                    print(f"  -> Produto criado: {details['cod']}")
                else:
                    print(f"  -> Produto já existe, ignorando: {details['cod']}")

            elif action == 'pair_product' or action == 'adjust_stock':
                cursor.execute(
                    'UPDATE products SET barcode = ?, estoque = ? WHERE cod = ?',
                    (details.get('newBarcode'), details.get('newStock'), details['cod'])
                )
                print(f"  -> Produto atualizado: {details['cod']}")

            elif action == 'create_user':
                cursor.execute("SELECT username FROM users WHERE username = ?", (details['username'],))
                if cursor.fetchone() is None:
                    cursor.execute(
                        'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                        (details['username'], details['password'], details['role'])
                    )
                    print(f"  -> Usuário criado: {details['username']}")
                else:
                    print(f"  -> Usuário já existe, ignorando: {details['username']}")

            elif action == 'create_sale':
                cursor.execute("SELECT timestamp FROM vendas_log WHERE timestamp = ?", (details['timestamp'],))
                if cursor.fetchone() is None:
                    # Formata a lista de produtos para uma string legível antes de salvar
                    produtos_str = ", ".join([f"{p['quantity']}x {p['name']}" for p in details['produtos']])
                    cursor.execute(
                        'INSERT INTO vendas_log (timestamp, vendedor, produtos, formas_pagamento, valores_pagos, desconto, valor_total) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (details['timestamp'], details['vendedor'], produtos_str, details['formas_pagamento'], details['valores_pagos'], details['desconto'], details['valor_total'])
                    )
                    print(f"  -> Venda registrada: {details['timestamp']}")
                else:
                    print(f"  -> Venda já existe, ignorando: {details['timestamp']}")
            
            # ATUALIZAÇÃO: Adiciona a lógica para excluir uma venda
            elif action == 'delete_sale':
                cursor.execute("DELETE FROM vendas_log WHERE timestamp = ?", (details['timestamp'],))
                if cursor.rowcount > 0:
                    print(f"  -> Venda excluída: {details['timestamp']}")
                else:
                    print(f"  -> Venda para excluir não encontrada, ignorando: {details['timestamp']}")

        except sqlite3.Error as e:
            print(f"  -> Erro no banco de dados ao processar a ação '{action}' para '{details}': {e}")

    conn.commit()

def main():
    """Função principal do script."""
    changes_json = os.environ.get('CHANGES_JSON')
    if not changes_json:
        print("Nenhuma alteração recebida. Apenas gerando o arquivo JSON.")
        changes_to_apply = []
    else:
        try:
            data = json.loads(changes_json)
            changes_to_apply = data.get('changes', [])
        except json.JSONDecodeError:
            print("Erro ao decodificar o JSON de alterações.")
            return

    conn = get_db_connection()
    
    if changes_to_apply:
        print(f"Processando {len(changes_to_apply)} alterações recebidas...")
        apply_changes_incrementally(conn, changes_to_apply)
    else:
        print("Nenhuma alteração para aplicar.")

    products, users, vendas_log = get_all_data(conn)
    
    json_output_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'dados_offline.json')
    version = "1.0.0"
    try:
        with open(json_output_path, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
            version_parts = current_data.get('version', '1.0.0').split('.')
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            version = ".".join(version_parts)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    output_data = {
        "version": version,
        "products": products,
        "users": users,
        "vendas_log": vendas_log
    }
    
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
        
    print(f"Arquivo 'dados_offline.json' atualizado com sucesso para a versão {version}")

    conn.close()

if __name__ == '__main__':
    main()
