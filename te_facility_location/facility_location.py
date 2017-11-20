from math import asin, cos, radians, sin, sqrt

import pkg_resources

from pulp import (
    LpInteger, LpMinimize, LpProblem, LpStatus, LpVariable, lpSum, value)

from simplekml import Icon, IconStyle, Kml, LineStyle, Style

from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.types import Float, Integer, Text

from tropofy.app import AppWithDataSets, Step, StepGroup
from tropofy.database.tropofy_orm import DataSetMixin
from tropofy.file_io import read_write_xl
from tropofy.widgets import Chart, ExecuteFunction, KMLMap, SimpleGrid


HEX_COLORS = [
    'FFFFFF00', 'FF00F5FF', 'FF00FA9A', 'FFC0FF3E', 'FFCAE1FF',
    'FFFCE6C9', 'FFEE6A50', 'FFFF6A6A', 'FF7171C6', 'FF71C671']

ICONS = {
    'blue': 'https://maps.google.com/mapfiles/kml/paddle/blu-circle-lv.png',
    'red': 'https://maps.google.com/mapfiles/kml/paddle/red-circle-lv.png'
}


# Models (aka DataSets)

class Shop(DataSetMixin):
    name = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    demand = Column(Integer, nullable=False)

    @classmethod
    def get_table_args(cls):
        return (UniqueConstraint('data_set_id', 'name'),)


class Plant(DataSetMixin):
    name = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)
    fixed_cost = Column(Integer, nullable=False)

    # See SQLAlchemy documentation on relationship.
    # (String used for class name as not yet defined here)
    flows = relationship('Flow', cascade='all')

    @classmethod
    def get_table_args(cls):
        return (UniqueConstraint('data_set_id', 'name'),)


class Flow(DataSetMixin):
    plant_name = Column(Text, nullable=False)
    shop_name = Column(Text, nullable=False)
    volume = Column(Float, nullable=False)

    shop = relationship(Shop)
    plant = relationship(Plant)

    @classmethod
    def get_table_args(cls):
        return (
            ForeignKeyConstraint(
                ['shop_name', 'data_set_id'],
                ['shop.name', 'shop.data_set_id'],
                ondelete='CASCADE',
                onupdate='CASCADE'
            ),
            ForeignKeyConstraint(
                ['plant_name', 'data_set_id'],
                ['plant.name', 'plant.data_set_id'],
                ondelete='CASCADE',
                onupdate='CASCADE'
            )
        )


# Widgets

plant_style = Style(
    iconstyle=IconStyle(scale=0.8, icon=Icon(href=ICONS['blue'])))

shop_style = Style(
    iconstyle=IconStyle(scale=0.4, icon=Icon(href=ICONS['red'])))


class KMLMapInput(KMLMap):

    def get_kml(self, app_session):

        kml = Kml()

        # set up map points for Plants

        plants_folder = kml.newfolder(name="Potential Facilities")
        plants_points = [
            plants_folder.newpoint(
                name=plant.name,
                coords=[(plant.longitude, plant.latitude)]
            ) for plant in app_session.data_set.query(Plant).all()
        ]

        for p in plants_points:
            p.style = plant_style

        # set up map points for Shops

        shops_folder = kml.newfolder(name="Shops")
        shops_points = [
            shops_folder.newpoint(
                name=shop.name,
                coords=[(shop.longitude, shop.latitude)]
            ) for shop in app_session.data_set.query(Shop).all()
        ]
        for p in shops_points:
            p.style = shop_style

        return kml.kml()


class KMLMapOutput(KMLMap):

    @staticmethod
    def get_cycled_hex_colour(n):
        return HEX_COLORS[n % 10]

    def get_kml(self, app_session):

        kml = Kml()
        flows = app_session.data_set.query(Flow).all()

        # set up points for Plants used

        plants_used = list(set([flow.plant for flow in flows]))

        plants_used_folder = kml.newfolder(name="Facilities Chosen")
        plants_used_points = [
            plants_used_folder.newpoint(
                name=plant.name,
                coords=[(plant.longitude, plant.latitude)]
            )
            for plant in plants_used
        ]
        for p in plants_used_points:
            p.style = plant_style

        # set up points for Plants not used

        plants_not_used_folder = kml.newfolder(name="Facilities Not Chosen")
        plants_not_used_points = [
            plants_not_used_folder.newpoint(
                name=plant.name,
                coords=[(plant.longitude, plant.latitude)]
            ) for plant in app_session.data_set.query(Plant).all()
            if plant not in plants_used
        ]
        for p in plants_not_used_points:
            p.style = plant_style

        for plant in plants_used:
            catchment_folder = kml.newfolder(
                name="Catchment for " + plant.name)
            catchment_points = [
                catchment_folder.newpoint(
                    name=shop.name,
                    coords=[(shop.longitude, shop.latitude)]
                ) for shop in [flow.shop for flow in plant.flows]
            ]
            for point in catchment_points:
                point.style = shop_style

            plant_location = catchment_folder.newpoint(
                name=plant.name, coords=[(plant.longitude, plant.latitude)])
            plant_location.style = plant_style
            catchment_line_style = Style(
                linestyle=LineStyle(
                    color=KMLMapOutput.get_cycled_hex_colour(
                        plants_used.index(plant)),
                    width=4
                )
            )
            catchment_lines = [catchment_folder.newlinestring(
                name='From: %s<br>To: %s<br>Flow: %s' %
                (flow.plant_name, flow.shop_name, flow.volume),
                coords=[
                    (flow.plant.longitude, flow.plant.latitude),
                    (flow.shop.longitude, flow.shop.latitude)
                ]) for flow in plant.flows
            ]
            for l in catchment_lines:
                l.style = catchment_line_style

        return kml.kml()


class PlantSizePieChart(Chart):
    def get_chart_type(self, app_session):
        return Chart.PIECHART

    def get_table_schema(self, app_session):
        return {"plant": ("string", "Plant"), "flow": ("number", "Flow")}

    def get_table_data(self, app_session):
        return [
            {
                "plant": plant.name,
                "flow": sum(flow.volume for flow in plant.flows)
            }
            for plant in app_session.data_set.query(Plant).all()
        ]

    def get_column_ordering(self, app_session):
        return ["plant", "flow"]

    def get_order_by_column(self, app_session):
        return "flow"

    def get_chart_options(self, app_session):
        return {'title': 'Relative Plants Sizes'}

# Execute Function Buttons


class ExecuteSolverFunction(ExecuteFunction):

    def get_button_text(self, app_session):
        return "Solve Facility Location Problem"

    def execute_function(self, app_session):
        msg = "You can only solve problems with 200 shops of fewer \
        using the free version of this app"
        if len(app_session.data_set.query(Shop).all()) > 200:
            app_session.task_manager.send_progress_message(msg)
        else:
            formulate_and_solve_facility_location_problem(app_session)


# Application

# Post code geocode data sourced from
# http://blog.orite.com.au/wp-content/uploads/2009/01/aupcgeo.7z
def load_brisbane_data(app_session):
    read_write_xl.ExcelReader.load_data_from_excel_file_on_disk(
        app_session,
        pkg_resources.resource_filename(
            'te_facility_location', 'facility_location_example_data.xlsx')
    )


class MyFacilityLocationSolverApp(AppWithDataSets):

    def get_name(self):
        return 'Facility Location Optimisation'

    def get_examples(self):
        return {"Demo data for Brisbane": load_brisbane_data}

    def get_static_content_path(self, app_session):
        pth = pkg_resources.resource_filename('te_facility_location', 'static')
        return pth

    def get_gui(self):
        step_group1 = StepGroup(name='Enter your data')
        step_group1.add_step(Step(
            name='Enter your locations',
            widgets=[SimpleGrid(Shop)],
            help_text="Enter the set of locations, with their associated \
            demand, that need to be serviced by a facility"
        ))
        step_group1.add_step(Step(
            name='Enter your candidate facilities',
            widgets=[SimpleGrid(Plant)],
            help_text="Enter the set of candidate facilities with their \
            capacities and commissioning costs"
        ))
        step_group1.add_step(Step(
            name='Review your data',
            widgets=[KMLMapInput()],
            help_text="Review the locations and candidate facilities entered \
            for correctness"
        ))

        step_group2 = StepGroup(name='Solve')
        step_group2.add_step(Step(name='Solve Facility Location Optimisation \
        Problem', widgets=[ExecuteSolverFunction()]))

        step_group3 = StepGroup(name='View the Solution')
        step_group3.add_step(Step(
            name='Download KML',
            widgets=[
                {"widget": SimpleGrid(Flow), "cols": 6},
                {"widget": PlantSizePieChart(), "cols": 6},
                {"widget": KMLMapOutput(), "cols": 12}
            ],
            help_text="The grid below shows the amount of product flowing \
            from facilities to locations. The map shows the same info \
            geographically."
        ))

        return [step_group1, step_group2, step_group3]

    def get_icon_url(self):
        return "/{}/static/{}/facility_location.png".format(
            self.url_name,
            self.get_app_version(),
        )

# Problem Solving


def haversine(lon1, lat1, lon2, lat2):
    r"""Calculate the great circle distance between two points on the earth.

    Distance is to be specified in decimal degrees.
    See: http://stackoverflow.com/questions/4913349/haversine-formula-in-\
    python-bearing-and-distance-between-two-gps-points
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km


def transportation_cost_per_unit(plant, shop):
    """Use the great circle distance with no multiplier to determine cost."""
    return haversine(
        plant.longitude, plant.latitude, shop.longitude, shop.latitude)


def formulate_and_solve_facility_location_problem(app_session):
    r"""Solve faclity location problem.

    This formulation (apart from one addition) is taken from the PuLP examples
    and adapted to use the Tropofy framework.
    See: http://pulp-or.googlecode.com/svn/trunk/pulp-or/examples/\
    ComputerPlantProblem.py
    Authors: Antony Phillips, Dr Stuart Mitchell 2007
    Used with permission.
    """
    # Send a progress message
    app_session.task_manager.send_progress_message("Commencing optimisation")

    shops = app_session.data_set.query(Shop).all()
    plants = app_session.data_set.query(Plant).all()

    # Creates a list of tuples containing all the possible routes for transport
    # between plants and shops
    routes = [(p, s) for p in plants for s in shops]

    # Creates the problem variables for the flow on the routes
    # from plants to shops
    flow = LpVariable.dicts("Route", (plants, shops), 0, None, LpInteger)

    # Creates the master problem variables of whether to
    # build the Plants or not
    build = LpVariable.dicts("BuildaPlant", plants, 0, 1, LpInteger)

    # Creates the 'prob' variable to contain the problem data
    prob = LpProblem("Facility Location Problem", LpMinimize)

    # The objective function is added to prob:
    # The sum of the transportation costs and the building fixed costs
    prob += lpSum([
        flow[p][s] * transportation_cost_per_unit(p, s) for (p, s) in routes
    ]) + lpSum([p.fixed_cost * build[p] for p in plants]), "Total Costs"

    # The Supply maximum constraints are added for each supply node (plant)
    for p in plants:
        prob += lpSum([
            flow[p][s] for s in shops
        ]) <= p.capacity * build[p], "Sum of Products out of Plant %s" % p.name

    # The Demand minimum constraints are added for each demand node (shop)
    for s in shops:
        prob += lpSum([
            flow[p][s] for p in plants
        ]) >= s.demand, "Sum of Products into Shops %s" % s.name

    # Add some extra constraints to improve integrality
    for (p, s) in routes:
        constraint = flow[p][s] <= s.demand * build[p]
        message = "Can not flow to shop %s from plant %s \
            unless it is built" % (s.name, p.name)
        prob += constraint, message

    # The problem is solved using PuLP's choice of Solver
    prob.solve()

    # Send a progress message
    app_session.task_manager.send_progress_message(
        "Status:" + LpStatus[prob.status])
    app_session.task_manager.send_progress_message(
        "Total Cost = " + str(value(prob.objective)))

    # Delete the previous solution
    app_session.data_set.query(Flow).delete()

    # add the solution
    for (p, s) in routes:
        if value(flow[p][s]) != 0:
            app_session.data_set.add(
                Flow(
                    plant_name=p.name,
                    shop_name=s.name,
                    volume=value(flow[p][s])
                )
            )

    # Send a some final progress messages
    app_session.task_manager.send_progress_message(
        "Finished, click 'View the Solution' on the left.")
