import psycopg2
from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QApplication, QMessageBox, QVBoxLayout
from PyQt5.uic import loadUi
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class AppLogic():
    def __init__(self):
        pass
    
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
        
    def closeEvent(self, event):
        """Cerrar la conexión al cerrar la ventana"""
        if self.connection:
            self.connection.close()
            print("Conexión cerrada")
        event.accept()
    

class ViewMain(QMainWindow, AppLogic):
    def __init__(self):
        super(ViewMain, self).__init__()
        loadUi(r"src\Ui\model2.ui", self)
        
        self.mPagos.setCurrentIndex(0)

        #Elementos Busqueda cliente
        self.btnSearchClient.clicked.connect(self.searchClients)
        
        self.tblClientes.setColumnWidth(0, 50)
        self.tblClientes.setColumnWidth(1, 200)
        self.tblClientes.setColumnWidth(2, 220)
        self.tblClientes.setColumnWidth(3, 250)
        
        self.tblDetalles.setColumnWidth(0, 75)
        self.tblDetalles.setColumnWidth(1, 75)
        self.tblDetalles.setColumnWidth(2, 75)
        self.tblDetalles.setColumnWidth(3, 100)
        self.tblDetalles.setColumnWidth(4, 200)
        self.tblDetalles.setColumnWidth(5, 200)
        
        
        self.connection = self.create_connection()
        self.loadClientData()
        
        self.tblClientes.cellClicked.connect(self.showDetails)
        
        # elemento agregar cliente
        self.btnSaveClient.clicked.connect(self.regiterNewClient)
        self.btnCleanClient.clicked.connect(self.cleanClientData)
        
        #obtener membresias en el combobox
        self.loadMembresias()
        
        #graficos
        self.frmPlotMPagos.setLayout(QVBoxLayout())  # Establecer un layout vertical en el frame
        self.graficarMetodoPago()
        self.btnRecargarMetodos.clicked.connect(self.graficarMetodoPago)
        
        self.frmPlotMembresias.setLayout(QVBoxLayout())  # Establecer un layout vertical en el frame
        self.graficarMembresias()
        self.btnRecargarMembresias.clicked.connect(self.graficarMembresias)
        
        self.frmPlotGanancias.setLayout(QVBoxLayout())  # Establecer un layout vertical en el frame
        self.graficarGananciasPorMes()
        self.btnRecargarGanancias.clicked.connect(self.graficarGananciasPorMes)
        
        
        
        
    def searchClients(self):
        criterio = self.lnNombre.text().strip()
        
        # Limpiar los resultados si no se ha hecho búsqueda
        self.tblClientes.setRowCount(0)
        
        if criterio == "":
            self.loadClientData()  # Cargar todos los datos
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
            
            self.fill_Client_table(resultados)
            
    def showDetails(self, row):
        """Obtiene el dato de la primera columna de la fila seleccionada"""
        id_dato = self.tblClientes.item(row, 0).text()  # Primera columna (ID)
        self.loadClientDetails(id_dato)
        
    def loadClientDetails(self, id_persona):
        #consulta para obtener los datos de una persona
        sqlquery = """SELECT
            pxm.id_contrato,
            m.nombre AS membresia,
            m.precio,
            m.tipo,
            pxm.fecha_registro,
            CONCAT(EXTRACT(YEAR FROM m.duracion), ' años ',
                EXTRACT(MONTH FROM m.duracion), ' meses ',
                EXTRACT(DAY FROM m.duracion), ' días') AS duracion
            FROM persona p
                    JOIN persona_x_membresia pxm ON pxm.id_persona = p.id_persona
                    JOIN membresias m ON pxm.id_membresia = m.id_membresia
            WHERE pxm.id_persona = (%s);"""
        
        resultados  = self.execute_query(sqlquery, (id_persona,))
        self.fillCLientDetails(resultados)
        
    def loadClientData(self):
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
        
        self.fill_Client_table(resultados)
        
    def fill_Client_table(self, resultados):
        """Llena la tabla con los resultados de la consulta"""
        self.tblClientes.setRowCount(len(resultados))
        tablerow = 0
        
        for row in resultados:
            self.tblClientes.setItem(tablerow, 0, QTableWidgetItem(str(row[0])))  # id_persona
            self.tblClientes.setItem(tablerow, 1, QTableWidgetItem(row[1]))  # nombre
            self.tblClientes.setItem(tablerow, 2, QTableWidgetItem(row[2]))  # telefono
            self.tblClientes.setItem(tablerow, 3, QTableWidgetItem(row[3]))  # correo
            tablerow += 1
    
    def fillCLientDetails(self, resultados):
        self.tblDetalles.setRowCount(len(resultados))
        tablerow = 0
        
        for row in resultados:
            self.tblDetalles.setItem(tablerow, 0, QTableWidgetItem(str(row[0])))
            self.tblDetalles.setItem(tablerow, 1, QTableWidgetItem(str(row[1])))
            self.tblDetalles.setItem(tablerow, 2, QTableWidgetItem(str(row[2])))
            self.tblDetalles.setItem(tablerow, 3, QTableWidgetItem(str(row[3])))
            self.tblDetalles.setItem(tablerow, 4, QTableWidgetItem(str(row[4])))
            self.tblDetalles.setItem(tablerow, 5, QTableWidgetItem(str(row[5])))
            tablerow += 1
    
    def regiterNewClient(self):
        nombre = self.lnNombre_2.text().strip()
        telefono = self.lnTelefono.text().strip()
        correo = self.lnCorreo.text().strip()
        
        if nombre == "" or telefono == "" or correo == "":
            self.mostrar_mensaje("Faltan datos", "Por favor, complete los campos.")
            return
        else:
            sqlquery = """
                INSERT INTO persona(nombre, telefono, correo)
                VALUES(%s, %s, %s);
            """
            self.execute_query(sqlquery, (nombre, telefono, correo))
            self.mostrar_mensaje("Cliente registrado", "El cliente fue registrado exitosamente.")
            self.loadClientData()
            self.cleanClientData()
                    
    def cleanClientData(self):
        self.lnNombre_2.setText("")
        self.lnTelefono.setText("")
        self.lnCorreo.setText("")
        
    def loadMembresias(self):
        sqlquery = "select concat(nombre ,' - ' , tipo, ' - ' , precio ) from membresias"
        membresias = self.execute_query(sqlquery)
        

        # Verificar si hay resultados antes de iterar
        if membresias:
            self.cmbMembresias.clear()
            for membresia in membresias:
                self.cmbMembresias.addItem(membresia[0])
        else:
            print("No hay membresías disponibles.")
        
    def mostrar_mensaje(self, titulo, mensaje):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def graficarMetodoPago(self):
        query = """SELECT metodo_pago, COUNT(*) AS cantidad
            FROM pagos
            GROUP BY metodo_pago
            ORDER BY cantidad DESC;"""
        
        df = pd.read_sql(query, self.connection)
        
        # Limpiar el QFrame de cualquier gráfico anterior
        for i in reversed(range(self.frmPlotMPagos.layout().count())):
            widget = self.frmPlotMPagos.layout().itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Crear el gráfico
        fig = plt.figure()  # Crear una nueva figura
        ax = fig.add_subplot(111)  # Crear un subplot en la figura
        ax.bar(df['metodo_pago'], df['cantidad'], color=['blue', 'red', 'green'])  # Gráfico de barras

        # Etiquetas y título
        ax.set_xlabel('Método de Pago')
        ax.set_ylabel('Cantidad de Pagos')
        ax.set_title('Distribución de Métodos de Pago')
        
        # Crear el canvas con la figura
        self.canvas = FigureCanvas(fig)
        
        # Agregar el canvas al layout del QFrame
        self.frmPlotMPagos.layout().addWidget(self.canvas)
        
        # Dibujar el gráfico en el canvas
        self.canvas.draw()

    def graficarMembresias(self):
        # Consulta para obtener los datos de membresía
        query = """SELECT
                    CONCAT(m.nombre, ' - ', m.tipo) AS membresia_tipo,
                    COUNT(*) AS total_contratos
                FROM persona_x_membresia pxm
                JOIN membresias m ON pxm.id_membresia = m.id_membresia
                GROUP BY membresia_tipo
                ORDER BY total_contratos DESC;"""
        
        # Ejecutar la consulta y obtener el DataFrame
        df = pd.read_sql(query, self.connection)
        
        # Limpiar el QFrame de cualquier gráfico anterior
        for i in reversed(range(self.frmPlotMembresias.layout().count())):
            widget = self.frmPlotMembresias.layout().itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Crear la figura y el gráfico
        fig = plt.figure()  # Crear una nueva figura
        ax = fig.add_subplot(111)  # Crear un subplot en la figura
        ax.bar(df['membresia_tipo'], df['total_contratos'], color=['blue', 'red', 'green'])  # Gráfico de barras

        # Etiquetas y título
        ax.set_xlabel('Membresía - Tipo')
        ax.set_ylabel('Total de Contratos')
        ax.set_title('Distribución de Membresías por Tipo')
        
        
        # Crear el canvas con la figura
        self.canvas = FigureCanvas(fig)
        
        # Agregar el canvas al layout del QFrame
        self.frmPlotMembresias.layout().addWidget(self.canvas)
        
        # Dibujar el gráfico en el canvas
        self.canvas.draw()

    def graficarGananciasPorMes(self):
        # Consulta SQL para obtener ganancias por mes
        query = """SELECT 
                    TO_CHAR(p.fecha_pago, 'YYYY-MM') AS mes,
                    SUM(m.precio) AS total_recaudado
                FROM pagos p
                JOIN persona_x_membresia pxm ON p.id_contrato = pxm.id_contrato
                JOIN membresias m ON pxm.id_membresia = m.id_membresia
                GROUP BY mes
                ORDER BY mes;"""
        
        # Ejecutar la consulta y obtener el DataFrame
        df = pd.read_sql(query, self.connection)
        
        # Limpiar el QFrame de cualquier gráfico anterior
        for i in reversed(range(self.frmPlotGanancias.layout().count())):
            widget = self.frmPlotGanancias.layout().itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Crear la figura y el gráfico
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.bar(df['mes'], df['total_recaudado'], color='green')

        # Etiquetas y título
        ax.set_xlabel('Mes')
        ax.set_ylabel('Total Recaudado')
        ax.set_title('Ganancias Recaudadas por Mes')

        # Rotar las etiquetas del eje X para mejorar la legibilidad
        plt.xticks(rotation=45)

        # Crear el canvas con la figura
        self.canvas = FigureCanvas(fig)
        
        # Agregar el canvas al layout del QFrame
        self.frmPlotGanancias.layout().addWidget(self.canvas)
        
        # Dibujar el gráfico en el canvas
        self.canvas.draw()

# aplicación principal
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = ViewMain()
    main.show()
    sys.exit(app.exec_())
