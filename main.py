from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, NoTransition

# Importación de módulos
from views.welcome import WelcomeScreen
from views.login import LoginScreen
from views.register_user import RegisterScreen
from views.dashboard import DashboardScreen
from views.pos import POSScreen
from views.checkout import CheckoutScreen
from views.inventory import InventoryScreen
from views.expenses import ExpensesScreen
from views.closure import ClosureScreen
from views.reports import ReportsScreen

import database

class VentaFacilApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Light"

        # Inicialización de la base de datos
        database.init_db()

        # Administrador central de pantallas
        self.sm = ScreenManager(transition=NoTransition())

        # Registro de todas las rutas de la app (incluyendo alias en español)
        self.sm.add_widget(WelcomeScreen(name="welcome"))
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(RegisterScreen(name="register"))
        self.sm.add_widget(DashboardScreen(name="dashboard"))
        self.sm.add_widget(POSScreen(name="pos"))
        self.sm.add_widget(CheckoutScreen(name="checkout"))
        self.sm.add_widget(InventoryScreen(name="inventory"))
        self.sm.add_widget(InventoryScreen(name="inventario"))
        self.sm.add_widget(ExpensesScreen(name="expenses"))
        self.sm.add_widget(ExpensesScreen(name="gastos"))
        self.sm.add_widget(ClosureScreen(name="closure"))
        self.sm.add_widget(ClosureScreen(name="cierre"))
        self.sm.add_widget(ReportsScreen(name="reports"))
        self.sm.add_widget(ReportsScreen(name="reportes"))

        return self.sm

if __name__ == "__main__":
    VentaFacilApp().run()