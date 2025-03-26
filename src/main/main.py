import psycopg2
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMainWindow, QApplication, QStackedWidget
from PyQt5.uic import loadUi
import sys

class mainView(QMainWindow):
    def __init__(self):
        super(mainView, self).__init__()
        loadUi(r"src\Ui\mainView.ui", self)
        
        self.actionBuscarCliente.triggered.connect(self.searchClients)
        
    def searchClients(self):
        searchClientsUI = SearchClientsUI()
        widget.addWidget(searchClientsUI)
        widget.setCurrentIndex(widget.currentIndex() + 1)


class SearchClientsUI(QWidget):
    def __init__(self):
        super(SearchClientsUI, self).__init__()
        loadUi(r"src\Ui\searchClients.ui", self)
        
        self.btnSearch.clicked.connect(self.searchClient)
        self.btnBack.clicked.connect(self.back)
        
        self.tableWidget.setColumnWidth(0, 50)
        self.tableWidget.setColumnWidth(1, 200)
        self.tableWidget.setColumnWidth(2, 220)
        self.tableWidget.setColumnWidth(3, 250)
        
        # Cargar los datos de la base de datos
        self.connection = self.create_connection()
        self.loadData()
    
    def create_connection(self):
        """Crea una conexión a la base de datos y la devuelve"""
        try:
            connection = psycopg2.connect(
                dbname="Gimnasio",
                user="postgres",
                password="1984",
                host="localhost",  # O la IP del servidor
                port="5432",
                client_encoding="UTF8"
            )
            print("Conexión exitosa")
            return connection
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            return None

    def execute_query(self, query, params=None):
        """Ejecuta una consulta SQL de forma segura"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al ejecutar la consulta: {e}")
            return []

    def searchClient(self):
        criterio = self.lnNombre.text().strip()
        
        # Limpiar los resultados si no se ha hecho búsqueda
        self.tableWidget.setRowCount(0)
        
        if criterio == "":
            self.loadData()  # Cargar todos los datos
            return
        else:
            # Consulta con LIKE para los tres casos diferentes
            sqlquery = """
                SELECT id_persona, nombre, telefono, correo
                FROM persona
                WHERE LOWER(nombre) LIKE LOWER(%s) OR nombre LIKE LOWER(%s) OR nombre LIKE LOWER(%s)
                LIMIT 20;
            """
            # Ejecutar la consulta con los parámetros correspondientes
            resultados = self.execute_query(sqlquery, ('%' + criterio + '%', criterio + '%', '%' + criterio))
            
            self.fill_table(resultados)

    def loadData(self):
        # Consulta para obtener los datos de personas con membresía
        sqlquery = """
            SELECT id_persona, nombre, telefono, correo 
            FROM persona
            WHERE id_persona IN (
                SELECT DISTINCT pxm.id_persona
                FROM persona p 
                JOIN persona_x_membresia pxm ON p.id_persona = pxm.id_persona
            )
            LIMIT 20;
        """
        resultados = self.execute_query(sqlquery)
        
        self.fill_table(resultados)

    def fill_table(self, resultados):
        """Llena la tabla con los resultados de la consulta"""
        self.tableWidget.setRowCount(len(resultados))
        tablerow = 0
        
        for row in resultados:
            self.tableWidget.setItem(tablerow, 0, QTableWidgetItem(str(row[0])))  # id_persona
            self.tableWidget.setItem(tablerow, 1, QTableWidgetItem(row[1]))  # nombre
            self.tableWidget.setItem(tablerow, 2, QTableWidgetItem(row[2]))  # telefono
            self.tableWidget.setItem(tablerow, 3, QTableWidgetItem(row[3]))  # correo
            tablerow += 1

    def closeEvent(self, event):
        """Cerrar la conexión al cerrar la ventana"""
        if self.connection:
            self.connection.close()
            print("Conexión cerrada")
        event.accept()
        
    def back(self):
        widget.setCurrentIndex(widget.currentIndex() - 1)



# aplicación principal
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    widget = QStackedWidget()
    window = mainView()
    widget.addWidget(window)
    widget.setFixedWidth(900)
    widget.setFixedHeight(600)
    widget.setWindowTitle("Gimnasio")
    widget.show()
    sys.exit(app.exec_())
