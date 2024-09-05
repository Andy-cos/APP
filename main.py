from flask import Flask
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import mysql.connector
from datetime import datetime, timedelta

# Configuración de la base de datos
db_config = {
    'host': 'junction.proxy.rlwy.net',
    'port': '39449',
    'user': 'root',
    'password': 'uahuKJRgFOXAWgYgIDSIGcvPJFkysVtI',
    'database': 'railway'
}

def get_data(start_date=None, end_date=None):
    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Consultar los datos en el rango de fechas
    query = """
        SELECT * FROM emeteorologicaps
        WHERE (%s IS NULL OR fecha >= %s) AND (%s IS NULL OR fecha <= %s)
    """
    cursor.execute(query, (start_date, start_date, end_date, end_date))
    rows = cursor.fetchall()

    # Organizar los datos por variable
    data = {key: [] for key in ['temperaturaaire', 'humedadaire', 'intensidadluz', 'indiceuv',
                                'velocidadviento', 'direccionviento', 'cantidadlluvia', 
                                'presionbarometrica']}
    timestamps = []
    
    for row in rows:
        timestamps.append(row.get('fecha', ''))
        for key in data.keys():
            data[key].append(row.get(key, 0))  # Append value or 0 if not present

    conn.close()
    return data, timestamps

# Inicializar la aplicación Flask
server = Flask(__name__)

# Crear la aplicación Dash
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)
app.title = "NOVA"

# Diseño de la aplicación Dash
app.layout = html.Div([
    html.Div(
        children=[
            html.Img(src='/assets/Nova.png', style={'height': '50px', 'margin-right': '10px'}),
            html.Span('Estación Meteorológica', style={'fontSize': '24px', 'fontWeight': 'bold'})
        ],
        style={'backgroundColor': 'green', 'color': 'white', 'display': 'flex', 'alignItems': 'center', 'padding': '10px', 'justifyContent': 'center'}
    ),
    dcc.Tabs([
        dcc.Tab(
            label='Supervisión',
            children=[
                html.Div([
                    html.H1('Variables de Estación Meteorológica', style={'textAlign': 'center'}),
                    html.Div(id='gauge-line-graphs', style={'display': 'flex', 'flexDirection': 'column'})
                ])
            ],
            style={'fontWeight': 'bold', 'fontSize': '20px'},
            selected_style={'fontWeight': 'bold', 'fontSize': '20px'}
        ),
        dcc.Tab(
            label='Históricos',
            children=[
                html.Div([
                    html.H2('Seleccionar Variables y Rango de Fechas', style={'textAlign': 'center'}),
                    html.Div([
                        html.Label('Seleccionar Variables:'),
                        dcc.Checklist(
                            id='variable-selector',
                            options=[
                                {'label': 'Temperatura Aire', 'value': 'temperaturaaire'},
                                {'label': 'Humedad Aire', 'value': 'humedadaire'},
                                {'label': 'Intensidad Luz', 'value': 'intensidadluz'},
                                {'label': 'Índice UV', 'value': 'indiceuv'},
                                {'label': 'Velocidad Viento', 'value': 'velocidadviento'},
                                {'label': 'Dirección Viento', 'value': 'direccionviento'},
                                {'label': 'Cantidad Lluvia', 'value': 'cantidadlluvia'},
                                {'label': 'Presión Barométrica', 'value': 'presionbarometrica'}
                            ],
                            value=['temperaturaaire']
                        )
                    ]),
                    html.Div([
                        html.Label('Seleccionar Rango de Fechas:'),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            start_date=datetime.now() - timedelta(days=1),
                            end_date=datetime.now(),
                            display_format='DD/MM/YYYY'
                        )
                    ]),
                    dcc.Graph(id='custom-graph')
                ])
            ],
            style={'fontWeight': 'bold', 'fontSize': '20px'},
            selected_style={'fontWeight': 'bold', 'fontSize': '20px'}
        )
    ])
])

@app.callback(
    Output('gauge-line-graphs', 'children'),
    [Input('gauge-line-graphs', 'children')]
)
def update_gauges_and_lines(_):
    start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    data, timestamps = get_data(start_date=start_date)

    # Define variable properties
    variables = {
        'temperaturaaire': {'name': 'Temperatura Aire', 'range': [-40, 100], 'unit': '°C', 'colors': {'normal': 'green', 'warning': 'yellow', 'danger': 'red'}, 'icon': '/assets/temperature_icon.png', 'thresholds': [10, 25, 50]},
        'humedadaire': {'name': 'Humedad Aire', 'range': [0, 100], 'unit': '%', 'colors': {'normal': 'green', 'warning': 'yellow', 'danger': 'red'}, 'icon': '/assets/humidity_icon.png', 'thresholds': [20, 60, 80]},
        'intensidadluz': {'name': 'Intensidad Luz', 'range': [0, 50000], 'unit': 'Lux', 'colors': {'normal': 'green', 'warning': 'yellow', 'danger': 'red'}, 'icon': '/assets/light_icon.png', 'thresholds': [10000, 25000, 50000]},
        'indiceuv': {'name': 'Índice UV', 'range': [0, 30], 'unit': '', 'colors': {'normal': 'green', 'warning': 'yellow', 'danger': 'red'}, 'icon': '/assets/uv_icon.png', 'thresholds': [10, 20, 30]},
        'velocidadviento': {'name': 'Velocidad Viento', 'range': [0, 50], 'unit': 'm/s', 'colors': {'normal': 'green', 'warning': 'yellow', 'danger': 'red'}, 'icon': '/assets/wind_speed_icon.png', 'thresholds': [0, 25, 50]},
        'direccionviento': {'name': 'Dirección Viento', 'range': [0, 360], 'unit': '°', 'colors': {'normal': 'lightblue', 'warning': 'blue', 'danger': 'purple'}, 'icon': '/assets/wind_direction_icon.png', 'thresholds': [180, 270, 360]},
        'cantidadlluvia': {'name': 'Cantidad Lluvia', 'range': [0, 30], 'unit': 'mm/h', 'colors': {'normal': 'green', 'warning': 'yellow', 'danger': 'red'}, 'icon': '/assets/rain_icon.png', 'thresholds': [10, 20, 30]},
        'presionbarometrica': {'name': 'Presión Barométrica', 'range': [0, 1100], 'unit': 'hPa', 'colors': {'normal': 'green', 'warning': 'yellow', 'danger': 'red'}, 'icon': '/assets/pressure_icon.png', 'thresholds': [540, 850, 1100]},
    }

    graphs = []
    for variable, props in variables.items():
        # Obtener el último valor de la variable
        last_value = data[variable][-1] if data[variable] else 0

        # Determinar el color del gauge
        if variable == 'temperaturaaire':
            if last_value > 30:
                color = props['colors']['warning']
            elif last_value > 50:
                color = props['colors']['danger']
            else:
                color = props['colors']['normal']
        elif variable == 'humedadaire':
            if last_value > 60:
                color = props['colors']['warning']
            elif last_value > 80:
                color = props['colors']['danger']
            else:
                color = props['colors']['normal']
        elif variable == 'intensidadluz':
            if last_value > 25000:
                color = props['colors']['warning']
            elif last_value > 50000:
                color = props['colors']['danger']
            else:
                color = props['colors']['normal']
        elif variable == 'indiceuv':
            if last_value > 20:
                color = props['colors']['warning']
            elif last_value > 30:
                color = props['colors']['danger']
            else:
                color = props['colors']['normal']
        elif variable == 'velocidadviento':
            if last_value > 25:
                color = props['colors']['warning']
            elif last_value > 50:
                color = props['colors']['danger']
            else:
                color = props['colors']['normal']
        elif variable == 'direccionviento':
            if last_value > 270:
                color = props['colors']['warning']
            elif last_value > 360:
                color = props['colors']['danger']
            else:
                color = props['colors']['normal']
        elif variable == 'cantidadlluvia':
            if last_value > 20:
                color = props['colors']['warning']
            elif last_value > 30:
                color = props['colors']['danger']
            else:
                color = props['colors']['normal']
        elif variable == 'presionbarometrica':
            if last_value > 850:
                color = props['colors']['warning']
            elif last_value > 1100:
                color = props['colors']['danger']
            else:
                color = props['colors']['normal']

        # Crear gauge
        gauge = dcc.Graph(
            id=f'gauge-{variable}',
            figure={
                'data': [go.Indicator(
                    mode="gauge+number",
                    value=last_value,
                    gauge={
                        'axis': {'range': props['range']},
                        'bar': {'color': color}
                    },
                    title={'text': f"{props['name']} ({props['unit']})"},
                    delta={'reference': 0},
                    domain={'x': [0, 1], 'y': [0, 1]},  # Ajustar el dominio del gráfico
                )],
                'layout': go.Layout(
                    height=400,  # Ajustar la altura
                    width=400,   # Ajustar el ancho
                    margin={'t': 30, 'b': 30, 'l': 30, 'r': 30},
                    images=[{
                        'source': props['icon'],
                        'xref': 'paper',
                        'yref': 'paper',
                        'x': 0.5,  # Centrado horizontal
                        'y': 0.55,  # Ajustar la posición vertical
                        'sizex': 0.1,  # Reducir el tamaño del icono
                        'sizey': 0.1,  # Reducir el tamaño del icono
                        'opacity': 0.8,
                        'layer': 'below'
                    }],
                    xaxis={'showgrid': True, 'showline': True},  # Añadir línea para el eje X
                    yaxis={'showgrid': True, 'showline': True}   # Añadir línea para el eje Y
                )
            }
        )

        # Crear gráfico de líneas
        line_graph = dcc.Graph(
            id=f'line-{variable}',
            figure={
                'data': [
                    go.Scatter(
                        x=timestamps,
                        y=data[variable],
                        mode='lines+markers',
                        name=f'{props["name"]} '
                    )
                ],
                'layout': go.Layout(
                    title=f'{props["name"]} ',
                    xaxis={'title': 'Fecha y Hora', 'showgrid': True, 'showline': True},  # Añadir línea para el eje X
                    yaxis={'title': f'{props["unit"]}', 'showgrid': True, 'showline': True},  # Añadir línea para el eje Y
                    height=300,
                    width=800
                )
            }
        )

        # Añadir la gráfica tipo gauge y la gráfica de líneas en una fila
        graphs.append(html.Div([gauge, line_graph], style={'display': 'flex', 'flexDirection': 'row', 'alignItems': 'center', 'margin': '10px'}))

    return graphs

@app.callback(
    Output('custom-graph', 'figure'),
    [
        Input('variable-selector', 'value'),
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date')
    ]
)
def update_custom_graph(selected_variables, start_date, end_date):
    data, timestamps = get_data(start_date=start_date, end_date=end_date)
    
    traces = []
    for variable in selected_variables:
        if variable in data:
            traces.append(go.Scatter(
                x=timestamps,
                y=data[variable],
                mode='lines',
                name=variable
            ))

    return {
        'data': traces,
        'layout': go.Layout(
            title='Datos Históricos',
            xaxis={'title': 'Fecha', 'showgrid': True, 'showline': True},  # Añadir línea para el eje X
            yaxis={'title': 'Valor', 'showgrid': True, 'showline': True},  # Añadir línea para el eje Y
            height=600,
            width=800
        )
    }

# Ejecutar el servidor Flask
if __name__ == '__main__':
    app.run_server(debug=True)

