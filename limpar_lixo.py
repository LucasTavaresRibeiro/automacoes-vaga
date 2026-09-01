import sqlite3

def limpar_banco():
    conn = sqlite3.connect('banco_vagas.db')
    cursor = conn.cursor()
    
    # Busca todas as vagas que não estão candidatadas
    cursor.execute("SELECT ID_Vaga, Titulo FROM vagas WHERE Status != 'Candidatado'")
    vagas = cursor.fetchall()
    
    termos_ti = ["analista", "suporte", "desenvolvedor", "python", "dados", "infraestrutura", "rpa", "helpdesk", "sistemas", "uipath", "low-code", "engenheiro", "programador", "tech", "ti", "tecnologia"]
    
    deletadas = 0
    for id_vaga, titulo in vagas:
        titulo_lower = titulo.lower()
        # Se nenhuma palavra de TI estiver no título, deleta
        if not any(t in titulo_lower for t in termos_ti):
            cursor.execute("DELETE FROM vagas WHERE ID_Vaga = ?", (id_vaga,))
            deletadas += 1
            
    # Deleta vagas que dizem CLT ou presencial na descrição que escaparam (apenas por garantia)
    cursor.execute("DELETE FROM vagas WHERE (Descricao LIKE '% clt %' OR Descricao LIKE '%presencial%') AND Status != 'Candidatado'")
    deletadas += cursor.rowcount
            
    conn.commit()
    conn.close()
    print(f"Limpeza concluída! Foram deletadas {deletadas} vagas inúteis.")

if __name__ == "__main__":
    limpar_banco()
