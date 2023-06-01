import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

st.set_page_config(page_title = 'La tienda de Fede Dashboard',
                    layout='wide',
                    initial_sidebar_state='collapsed')

# Lectura y filtrado de csv's

df = pd.read_csv('data/st_tabla_totalesycantidad.csv')
df_articulos = pd.read_csv('data/df_articulos_ST.csv')
df_rubros = pd.read_csv('data/df_rubros_ST.csv')
metodos = pd.read_csv('data/metodospago.csv')

### MERGEO Y FILTRADO DE DATAFRAMES PARA SEGUNDA TAB

tabla_totales = df.copy()
column_name_mapping = {
    'id': 'notaventa',
    'total': 'monto',
}
tabla_totales = tabla_totales.rename(columns=column_name_mapping)
merged_df = tabla_totales.merge(metodos, on='notaventa', how='left')
merged_df['monto_x'] = merged_df['monto_x'].fillna(merged_df['monto_y'])
merged_df = merged_df.drop(['monto_y', 'id', 'tipo'], axis=1)
merged_df = merged_df.rename(columns={'monto_x': 'total'})
df_tab2 = merged_df[merged_df['notaventa'] >= 21553]
df_tab2 = df_tab2[df_tab2['cantidad_articulos'] <= 10]
df_tab2['horas'] = pd.to_datetime(df_tab2['fecha'], format="%Y-%m-%d %H:%M:%S").dt.hour

from pandas.api.types import CategoricalDtype

cat_day_of_week = CategoricalDtype(
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 
    ordered=True
)
cat_month = CategoricalDtype(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], 
    ordered=True)

st.title('La tienda de Fede Dashboard')

tab_titles = [
                "General",
                "Rubros",
                "Artículos",
                "Horarios",
                "Métodos de pago"

]

tabs = st.tabs(tab_titles)

with tabs[0]:
    anio_filter = st.multiselect(label= 'Seleccione Año',
                                options=df['ANIO'].unique(),
                                default=df['ANIO'].unique())
    df1 = df.query('ANIO == @anio_filter')
    df_articulos1 = df_articulos.query('ANIO == @anio_filter')
    df_rubros1 = df_rubros.query('ANIO == @anio_filter')
    mes_filter = st.multiselect(label='Seleccione Mes',
                            options=df1['MES'].unique(),
                            default=df1['MES'].unique())
    # QUERY

    df2 = df1.query('MES == @mes_filter')
    df_articulos2 = df_articulos1.query('MES == @mes_filter')
    df_rubros2 = df_rubros1.query('MES == @mes_filter')
    evo_rubros = df_rubros2.groupby(['fecha','ANIO', 'MES'])['rubro'].value_counts().reset_index(name='cant_rubro')

    ### ARMO KPI'S

    total_ingresos = int(df2['total'].sum())
    cantidad_ventas = len(df2)
    promedio_venta = int(total_ingresos/cantidad_ventas)
    cantidad_articulos = int(df2['cantidad_articulos'].sum())
    promedio_articulos = f"{total_ingresos/cantidad_articulos:.2f}"
    articulos_por_venta = f"{cantidad_articulos/cantidad_ventas:.2f}"

    def format_number(number):
        suffixes = ['', 'K', 'M', 'B', 'T']
        magnitude = 0
        while abs(number) >= 1000:
            number /= 1000.0
            magnitude += 1
        return f"{number:.2f}{suffixes[magnitude]}"

    ### ARMO COLUMNAS CON METRICAS

    col1, col2, col3= st.columns(3)

    with col1: 
        st.metric(
            label='Total de ingresos',
            value=format_number(total_ingresos)
        )

    with col2: 
        st.metric(
            label='Cantidad de ventas',
            value=cantidad_ventas
        )

    with col3: 
        st.metric(
            label='Promedio de $ por venta',
            value=promedio_venta
        )

    col4, col5, col6= st.columns(3)

    with col4: 
        st.metric(
            label='Cantidad de articulos vendidos',
            value=cantidad_articulos
        )
    with col5: 
        st.metric(
            label='Promedio de $ por articulo',
            value=promedio_articulos
        )
    with col6: 
        st.metric(
            label='Cantidad de articulos por venta',
            value=articulos_por_venta
        )

    ### ARMO GRAFICOS

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:

        # Histograma de ingresos

        fig_ingresos = px.histogram(df2, x="fecha", y="total", histfunc="sum", title="<b>Total de ingresos<b>")
        fig_ingresos.update_traces(xbins_size="M1", hovertemplate='Período: %{x}<br>Ingresos: %{y:,.2s}')
        fig_ingresos.update_xaxes(showgrid=False, ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
        fig_ingresos.update_layout(bargap=0.1, xaxis_title='Fecha', yaxis_title='Ingresos (en millones)')
        st.plotly_chart(fig_ingresos)

        # Bar chart crecimiento mensual porcentual 

        df2['fecha'] = pd.to_datetime(df2['fecha']) 
        df2['month'] = df2['fecha'].dt.strftime('%Y-%m')

        df_groupedd = df2.groupby('month')['total'].sum().reset_index() 
        df_groupedd['variacion_ingreso'] = df_groupedd['total'].pct_change() * 100 
        fig_growthh = px.bar(df_groupedd, x='month', y='variacion_ingreso', text_auto=True, labels={'month': 'Mes'},
                    title='Variación mensual de los ingresos')

        fig_growthh.update_traces(textfont_size=24, textangle=0, textposition="outside", cliponaxis=False, hovertemplate='Mes: %{x}<br>Variación del ingreso (%): %{y:.2f}', texttemplate='%{y:.2f}')
        fig_growthh.update_xaxes(showgrid=False, ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
        fig_growthh.update_layout(bargap=0.1, xaxis_title='Fecha', yaxis_title='Variación del ingreso (%)')
        st.plotly_chart(fig_growthh)
        
        # Bar chart top 5 articulos
        df_top5_art = df_articulos2
        df_top5_art_top = df_top5_art.groupby('producto').agg({"cant_prod" : "sum"}).reset_index().sort_values(by='cant_prod', ascending=True)[-5:]
        fig_top5_art= go.Figure()

        fig_top5_art.add_trace(
                        go.Bar(x=df_top5_art_top['cant_prod'], y=df_top5_art_top['producto'], name='producto', text=df_top5_art_top['cant_prod'], orientation='h'))
        fig_top5_art.update_layout(title="<b>Top 5 artículos<b>")
        fig_top5_art.update_traces(hovertemplate='Artículo: %{y}<br>Cantidad vendida: %{x}', hoverlabel=dict(namelength=0))
        st.plotly_chart(fig_top5_art)

        # Bar chart top 5 rubros

        df_top5_rubros = evo_rubros.groupby('rubro').agg({"cant_rubro" : "sum"}).reset_index().sort_values(by='cant_rubro', ascending=True)[-5:]
        fig_top5_rubros= go.Figure()

        fig_top5_rubros.add_trace(
                        go.Bar(x=df_top5_rubros['cant_rubro'], y=df_top5_rubros['rubro'], name='rubro', text=df_top5_rubros['cant_rubro'], orientation='h'))
        fig_top5_rubros.update_layout(title="<b>Top 5 rubros<b>")
        fig_top5_rubros.update_traces(hovertemplate='Rubro: %{y}<br>Artículos vendidos del rubro: %{x}', hoverlabel=dict(namelength=0))
        st.plotly_chart(fig_top5_rubros)


    with col_graf2:

        # Histograma cantidad de ventas
        df3 = df2
        df3['cantidad_ventas'] = 1
        fig_ingresos2 = px.histogram(df_articulos2, x="fecha", y="cant_prod", histfunc="sum", title="<b>Cantidad de ventas<b>")
        fig_ingresos2.update_traces(xbins_size="M1", hovertemplate='Período: %{x}<br>Ventas: %{y}')
        fig_ingresos2.update_xaxes(showgrid=False, ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
        fig_ingresos2.update_layout(bargap=0.1, xaxis_title='Fecha', yaxis_title='Cantidad de ventas')
        st.plotly_chart(fig_ingresos2)

        # Histograma de articulos vendidos
        fig_articulos_vendidos = px.histogram(df2, x="fecha", y="cantidad_articulos", histfunc="sum", title="<b>Total de artículos vendidos<b>")
        fig_articulos_vendidos.update_traces(xbins_size="M1", hovertemplate='Período: %{x}<br>Artículos vendidos: %{y}')
        fig_articulos_vendidos.update_xaxes(showgrid=False, ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
        fig_articulos_vendidos.update_layout(bargap=0.1, xaxis_title='Fecha', yaxis_title='Cantidad de artículos vendidos')
        st.plotly_chart(fig_articulos_vendidos)

        # Bar chart representacion porcentual articulos

        repre_porc_art = df_rubros2.groupby('producto').agg({"total" : "sum"}).reset_index().sort_values(by='total', ascending=True)
        repre_porc_art['articulo_percentage'] = repre_porc_art['total'].apply(lambda x: (x/repre_porc_art['total'].sum())*100)
        repre_porc_art = repre_porc_art.sort_values(by='articulo_percentage', ascending=True)[-5:]

        fig_repre_porc_art= go.Figure()

        fig_repre_porc_art.add_trace(
                        go.Bar(x=repre_porc_art['articulo_percentage'], y=repre_porc_art['producto'], name='producto', text=repre_porc_art['articulo_percentage'].round(2), orientation='h'))
        fig_repre_porc_art.update_layout(title="<b>Top 5 artículos en representación porcentual del total de ingresos<b>")
        fig_repre_porc_art.update_traces(hovertemplate='Artículo: %{y}<br>Representación porcentual de los ingresos: %{x:.2f}', hoverlabel=dict(namelength=0))
        st.plotly_chart(fig_repre_porc_art)

        # Bar chart representacion porcentual rubros
        repre_porc_rubro = df_rubros2.groupby('rubro').agg({"total" : "sum"}).reset_index().sort_values(by='total', ascending=True)
        repre_porc_rubro['rubro_percentage'] = repre_porc_rubro['total'].apply(lambda x: (x/repre_porc_rubro['total'].sum())*100)
        repre_porc_rubro = repre_porc_rubro.sort_values(by='rubro_percentage', ascending=True)[-5:]

        fig_repre_porc_rubro= go.Figure()

        fig_repre_porc_rubro.add_trace(
                        go.Bar(x=repre_porc_rubro['rubro_percentage'], y=repre_porc_rubro['rubro'], name='rubro', text=repre_porc_rubro['rubro_percentage'].round(2), orientation='h'))
        fig_repre_porc_rubro.update_layout(title="<b>Top 5 rubros en representación porcentual del total de ingresos<b>")
        fig_repre_porc_rubro.update_traces(hovertemplate='Rubro: %{y}<br>Representación porcentual de los ingresos: %{x:.2f}', hoverlabel=dict(namelength=0))
        st.plotly_chart(fig_repre_porc_rubro)

### GRAFICOS

df_grouped = df_tab2.groupby([df_tab2['MES'], df_tab2['horas']]).agg({'total': 'sum'}).reset_index()
df_grouped['formatted_value'] = df_grouped['total'].apply(lambda x: '{:.1f}M'.format(x / 1e6) if x >= 1e6 else '{:.1f}K'.format(x / 1e3))
df_grouped['MES'] = df_grouped['MES'].astype(cat_month)
df_grouped = df_grouped.sort_values(['MES', 'horas'], ascending=False)
df_grouped['MES'] = df_grouped['MES'].astype(object)

df_ingresos_dia = df_tab2.groupby([df_tab2['DIA'], df_tab2['horas']]).agg({'total': 'sum'}).reset_index()
df_ingresos_dia['formatted_value'] = df_ingresos_dia['total'].apply(lambda x: '{:.1f}M'.format(x / 1e6) if x >= 1e6 else '{:.1f}K'.format(x / 1e3))
df_ingresos_dia['DIA'] = df_ingresos_dia['DIA'].astype(cat_day_of_week)
df_ingresos_dia = df_ingresos_dia.sort_values(['DIA', 'horas'], ascending=False)
df_ingresos_dia['DIA'] = df_ingresos_dia['DIA'].astype(object)


df_cantidad_ventas = df_tab2.groupby([df_tab2['MES'], df_tab2['horas']]).agg({'total': 'count'}).reset_index()
df_cantidad_ventas['MES'] = df_cantidad_ventas['MES'].astype(cat_month)
df_cantidad_ventas = df_cantidad_ventas.sort_values(['MES', 'horas'], ascending=False)
df_cantidad_ventas['MES'] = df_cantidad_ventas['MES'].astype(object)

df_cantidad_ventas_dia = df_tab2.groupby([df_tab2['DIA'], df_tab2['horas']]).agg({'total': 'count'}).reset_index()
df_cantidad_ventas_dia['DIA'] = df_cantidad_ventas_dia['DIA'].astype(cat_day_of_week)
df_cantidad_ventas_dia = df_cantidad_ventas_dia.sort_values(['DIA', 'horas'], ascending=False)
df_cantidad_ventas_dia['DIA'] = df_cantidad_ventas_dia['DIA'].astype(object)

df_cantidad_articulos = df_tab2.groupby([df_tab2['MES'], df_tab2['horas']]).agg({'cantidad_articulos': 'sum'}).reset_index()
df_cantidad_articulos['MES'] = df_cantidad_articulos['MES'].astype(cat_month)
df_cantidad_articulos = df_cantidad_articulos.sort_values(['MES', 'horas'], ascending=False)
df_cantidad_articulos['MES'] = df_cantidad_articulos['MES'].astype(object)

df_cantidad_articulos_dia = df_tab2.groupby([df_tab2['DIA'], df_tab2['horas']]).agg({'cantidad_articulos': 'sum'}).reset_index()
df_cantidad_articulos_dia['DIA'] = df_cantidad_articulos_dia['DIA'].astype(cat_day_of_week)
df_cantidad_articulos_dia = df_cantidad_articulos_dia.sort_values(['DIA', 'horas'], ascending=False)
df_cantidad_articulos_dia['DIA'] = df_cantidad_articulos_dia['DIA'].astype(object)

with tabs[1]:
    df_tab1 = df_rubros.copy()
    anio_filtro = st.multiselect(label= 'Seleccione un Año',
                                options=df_tab1['ANIO'].unique(),
                                default=df_tab1['ANIO'].unique())
    mes_filtro = st.multiselect(label='Seleccione un Mes',
                            options=df_tab1['MES'].unique(),
                            default=df_tab1['MES'].unique())
    df_final_tab1 = df_tab1.query('ANIO == @anio_filtro & MES == @mes_filtro')
    cant_rubros = df_final_tab1.groupby('fecha')['rubro'].value_counts().reset_index(name='cant_rubro')
    col_1_rubro, col_2_rubro = st.columns(2)
    with col_1_rubro:
        df_top5_rubros_tab = cant_rubros.groupby('rubro').agg({"cant_rubro" : "sum"}).reset_index().sort_values(by='cant_rubro', ascending=True)[-5:]
        fig_top5_rubros_tab= go.Figure()

        fig_top5_rubros_tab.add_trace(
                        go.Bar(x=df_top5_rubros_tab['cant_rubro'], y=df_top5_rubros_tab['rubro'], name='rubro', text=df_top5_rubros_tab['cant_rubro'], orientation='h'))
        fig_top5_rubros_tab.update_layout(title="<b>Top 5 rubros<b>")
        fig_top5_rubros_tab.update_traces(hovertemplate='Rubro: %{y}<br>Artículos vendidos del rubro: %{x}', hoverlabel=dict(namelength=0))
        st.plotly_chart(fig_top5_rubros_tab)

    with col_2_rubro:
        
        repre_porc_rubro_tab = df_final_tab1.groupby('rubro').agg({"total" : "sum"}).reset_index().sort_values(by='total', ascending=True)
        repre_porc_rubro_tab['rubro_percentage'] = repre_porc_rubro_tab['total'].apply(lambda x: (x/repre_porc_rubro_tab['total'].sum())*100)
        repre_porc_rubro_tab = repre_porc_rubro_tab.sort_values(by='rubro_percentage', ascending=True)[-5:]

        fig_repre_porc_rubro_tab= go.Figure()

        fig_repre_porc_rubro_tab.add_trace(
                        go.Bar(x=repre_porc_rubro_tab['rubro_percentage'], y=repre_porc_rubro_tab['rubro'], name='rubro', text=repre_porc_rubro_tab['rubro_percentage'].round(2), orientation='h'))
        fig_repre_porc_rubro_tab.update_layout(title="<b>Top 5 rubros en representación porcentual del total de ingresos<b>")
        fig_repre_porc_rubro_tab.update_traces(hovertemplate='Rubro: %{y}<br>Representación porcentual de los ingresos: %{x:.2f}', hoverlabel=dict(namelength=0))
        st.plotly_chart(fig_repre_porc_rubro_tab)

    df_sorteado_rubro = df_tab1.copy()
    df_sorteado_rubro = df_sorteado_rubro.sort_values('rubro')

    rubro_filtro = st.multiselect(label='Seleccione uno o más rubros',
                            options=df_sorteado_rubro['rubro'].unique(),
                            default=[])
    df_final_tab2 = df_final_tab1.query('rubro == @rubro_filtro')
    cant_rubros2 = cant_rubros.query('rubro == @rubro_filtro')
    col_3_rubro, col_4_rubro = st.columns(2)
    with col_3_rubro: 
        df_final_tab2['fecha'] = pd.to_datetime(df_final_tab2['fecha'])
        df_linechart = df_final_tab2.groupby(['rubro', pd.Grouper(key='fecha', freq='M')])['total'].sum().reset_index()
        fig_linechart_rubro = px.line(df_linechart, x='fecha', y='total', color='rubro', markers=True, title = 'Ingresos según rubro')
        fig_linechart_rubro.update_xaxes(showgrid=False, ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
        fig_linechart_rubro.update_layout(xaxis_title='Fecha', yaxis_title='Ingresos (en millones)', legend_title='<br>Rubro<br>', hovermode="x unified")
        fig_linechart_rubro.update_traces(hovertemplate='<br>Fecha: %{x}<br>Ingresos: %{y:,.2s}')
        st.plotly_chart(fig_linechart_rubro)

    with col_4_rubro:
        cant_rubros2['fecha'] = pd.to_datetime(cant_rubros2['fecha'])
        df_linechart2 = cant_rubros2.groupby(['rubro', pd.Grouper(key='fecha', freq='M')])['cant_rubro'].sum().reset_index()
        fig_linechart_rubro2 = px.line(df_linechart2, x='fecha', y='cant_rubro', color='rubro', markers=True, title = 'Cantidad ventas según rubro')
        fig_linechart_rubro2.update_xaxes(showgrid=False, ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
        fig_linechart_rubro2.update_layout(xaxis_title='Fecha', yaxis_title='Cantidad de ventas', legend_title='<br>Rubro<br>', hovermode="x unified")
        fig_linechart_rubro2.update_traces(hovertemplate='<br>Fecha: %{x}<br>Cantidad de ventas: %{y}')
        st.plotly_chart(fig_linechart_rubro2)
        

with tabs[2]:
    anio_filtros = st.multiselect(label= 'Seleccionar un Año',
                                options=df_tab1['ANIO'].unique(),
                                default=df_tab1['ANIO'].unique())
    mes_filtros = st.multiselect(label='Seleccionar un Mes',
                            options=df_tab1['MES'].unique(),
                            default=df_tab1['MES'].unique())
    df_final_tab2_producto = df_tab1.query('ANIO == @anio_filtros & MES == @mes_filtros')
    col_1_producto, col_2_producto = st.columns(2)
    with col_1_producto:
        df_top5_producto = df_final_tab2_producto.copy()
        df_top5_producto = df_top5_producto.groupby('producto').agg({"cantidad" : "sum"}).reset_index().sort_values(by='cantidad', ascending=True)[-5:]
        fig_top5_producto= go.Figure()

        fig_top5_producto.add_trace(
                        go.Bar(x=df_top5_producto['cantidad'], y=df_top5_producto['producto'], name='producto', text=df_top5_producto['cantidad'], orientation='h'))
        fig_top5_producto.update_layout(title="<b>Top 5 artículos<b>")
        fig_top5_producto.update_traces(hovertemplate='Artículo: %{y}<br>Cantidad vendida: %{x}', hoverlabel=dict(namelength=0))
        st.plotly_chart(fig_top5_producto)

    with col_2_producto:
        
        repre_porc_articulo = df_final_tab2_producto.groupby('producto').agg({"total" : "sum"}).reset_index().sort_values(by='total', ascending=True)
        repre_porc_articulo['articulo_percentage'] = repre_porc_articulo['total'].apply(lambda x: (x/repre_porc_articulo['total'].sum())*100)
        repre_porc_articulo = repre_porc_articulo.sort_values(by='articulo_percentage', ascending=True)[-5:]

        fig_repre_porc_articulo= go.Figure()

        fig_repre_porc_articulo.add_trace(
                        go.Bar(x=repre_porc_articulo['articulo_percentage'], y=repre_porc_articulo['producto'], name='producto', text=repre_porc_articulo['articulo_percentage'].round(2), orientation='h'))
        fig_repre_porc_articulo.update_layout(title="<b>Top 5 artículos en representación porcentual del total de ingresos<b>")
        fig_repre_porc_articulo.update_traces(hovertemplate='Artículo: %{y}<br>Representación porcentual de los ingresos: %{x:.2f}', hoverlabel=dict(namelength=0))
        st.plotly_chart(fig_repre_porc_articulo)

    producto_sorteado = df_tab1
    producto_sorteado['producto'] = producto_sorteado['producto'].str.lower()
    producto_sorteado['producto'] = producto_sorteado['producto'].str.capitalize()
    producto_sorteado = producto_sorteado.sort_values('producto')

    producto_filtro = st.multiselect(label='Seleccione uno o más artículos',
                            options=producto_sorteado['producto'].unique(),
                            default=[])
    
    df_final_tab2_productos = df_final_tab2_producto.query('producto == @producto_filtro')

    col_3_producto, col_4_producto = st.columns(2)

    with col_3_producto: 
        df_final_tab2_productos['fecha'] = pd.to_datetime(df_final_tab2_productos['fecha'])
        df_linechart_prod1 = df_final_tab2_productos.groupby(['producto', pd.Grouper(key='fecha', freq='M')])['total'].sum().reset_index()
        fig_linechart_prod1 = px.line(df_linechart_prod1, x='fecha', y='total', color='producto', markers=True, title = 'Ingresos según artículo')
        fig_linechart_prod1.update_xaxes(showgrid=False, ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
        fig_linechart_prod1.update_layout(xaxis_title='Fecha', yaxis_title='Ingresos (en millones)', legend_title='<br>Artículo<br>', hovermode="x unified")
        fig_linechart_prod1.update_traces(hovertemplate='<br>Fecha: %{x}<br>Ingresos: %{y:,.2s}')
        st.plotly_chart(fig_linechart_prod1)

    with col_4_producto:
        df_linechart_prod2 = df_final_tab2_productos.groupby(['producto', pd.Grouper(key='fecha', freq='M')])['cantidad'].sum().reset_index()
        fig_linechart_prod2 = px.line(df_linechart_prod2, x='fecha', y='cantidad', color='producto', markers=True, title = 'Cantidad ventas según artículo')
        fig_linechart_prod2.update_xaxes(showgrid=False, ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
        fig_linechart_prod2.update_layout(xaxis_title='Fecha', yaxis_title='Cantidad de artículos vendidos', legend_title='<br>Artículo<br>', hovermode="x unified")
        fig_linechart_prod2.update_traces(hovertemplate='<br>Fecha: %{x}<br>Artículos vendidos: %{y}')
        st.plotly_chart(fig_linechart_prod2)

with tabs[3]:
    col_mes, col_dia = st.columns(2)
    with col_mes:
        st.write("**Clasificado por mes**")
        mes_hora = go.Figure()
        mes_hora.add_trace(go.Heatmap(
                        z=df_grouped.total,
                        x=df_grouped.horas,
                        y=df_grouped.MES,
                        hoverongaps = False,
                        colorscale=[[0, "#caf3ff"], [1, "#2c82ff"]], texttemplate="%{z}", hovertemplate='Ingresos: %{text}<extra></extra>',
                        ))
        mes_hora.update_traces(text=df_grouped['formatted_value'])
        mes_hora.add_trace(go.Heatmap(
                        z=df_cantidad_ventas.total,
                        x=df_cantidad_ventas.horas,
                        y=df_cantidad_ventas.MES,
                        hoverongaps = False,
                        colorscale=[[0, "#caf3ff"], [1, "#2c82ff"]], texttemplate="%{z}", visible=False, hovertemplate='Total de ventas: %{z}<extra></extra>'
                        ))
        mes_hora.add_trace(go.Heatmap(
                        z=df_cantidad_articulos.cantidad_articulos,
                        x=df_cantidad_articulos.horas,
                        y=df_cantidad_articulos.MES,
                        hoverongaps = False,
                        colorscale=[[0, "#caf3ff"], [1, "#2c82ff"]], texttemplate="%{z}", visible=False, hovertemplate='Artículos vendidos: %{z}<extra></extra>'
                        ))
        mes_hora.update_layout(dict(
        margin=dict(l=10, b=10, t=10, r=10),
        modebar={"orientation": "v"},
        font=dict(family="Open Sans", size=14),
        xaxis=dict(
            side="bottom",
            ticks="",
            ticklen=2,
            tickfont=dict(family="sans-serif"),
            tickcolor="#ffffff",
            tickmode='linear',  
            dtick=1
        ),
        yaxis=dict(
            side="left", ticks="", tickfont=dict(family="sans-serif"), ticksuffix=" "
        ),
        hovermode="closest",
        showlegend=False,
    ),
            updatemenus=[
                dict(
                    xanchor='left',
                    x=-0.17,
                    yanchor='top',
                    y=1.3,
                    active=0,
                    buttons=list([
                        dict(label="Ingresos por mes por hora",
                            method="update",
                            args=[{"visible": [True, False, False]}]
                            ),
                        dict(label="Ventas por mes por hora",
                            method="update",
                            args=[{"visible": [False, True, False]}]
                            ),
                        dict(label="Artículos por mes por hora",
                            method="update",
                            args=[{"visible": [False, False, True]}]
                            )
                    ]),
                )
            ])
        st.plotly_chart(mes_hora, use_container_width=True)
        
        with col_dia:
            st.write("**Clasificado por dia**")
            dia_hora = go.Figure()

            dia_hora.add_trace(go.Heatmap(
                            z=df_ingresos_dia.total,
                            x=df_ingresos_dia.horas,
                            y=df_ingresos_dia.DIA,
                            hoverongaps = True,
                            colorscale=[[0, "#caf3ff"], [1, "#2c82ff"]], texttemplate="%{z}", showlegend=False, hovertemplate='Ingresos: %{text}<extra></extra>',
                            ))
            dia_hora.update_traces(text=df_ingresos_dia['formatted_value'])
            dia_hora.add_trace(go.Heatmap(
                            z=df_cantidad_ventas_dia.total,
                            x=df_cantidad_ventas_dia.horas,
                            y=df_cantidad_ventas_dia.DIA,
                            hoverongaps = False,
                            colorscale=[[0, "#caf3ff"], [1, "#2c82ff"]], texttemplate="%{z}", visible=False, hovertemplate='Total de ventas: %{z}<extra></extra>'
                            ))
            dia_hora.add_trace(go.Heatmap(
                            z=df_cantidad_articulos_dia.cantidad_articulos,
                            x=df_cantidad_articulos_dia.horas,
                            y=df_cantidad_articulos_dia.DIA,
                            hoverongaps = False,
                            colorscale=[[0, "#caf3ff"], [1, "#2c82ff"]], texttemplate="%{z}", visible=False, hovertemplate='Artículos vendidos: %{z}<extra></extra>'
                            ))


            dia_hora.update_layout(dict(
        margin=dict(l=10, b=10, t=10, r=10),
        modebar={"orientation": "v"},
        font=dict(family="Open Sans", size=14),
        xaxis=dict(
            side="bottom",
            ticks="",
            ticklen=2,
            tickfont=dict(family="sans-serif"),
            tickcolor="#ffffff",
            tickmode='linear',  
            dtick=1
        ),
        yaxis=dict(
            side="left", ticks="", tickfont=dict(family="sans-serif"), ticksuffix=" "
        ),
        hovermode="closest",
        showlegend=False,
    ),
                updatemenus=[
                    dict(
                        xanchor='left',
                        x=-0.17,
                    yanchor='top',
                    y=1.3,
                        active=0,
                        buttons=list([
                            dict(label="Ingresos por día por hora",
                                method="update",
                                args=[{"visible": [True, False, False]}]
                                ),
                            dict(label="Ventas por día por hora",
                                method="update",
                                args=[{"visible": [False, True, False]}]
                                ),
                            dict(label="Artículos por día por hora",
                                method="update",
                                args=[{"visible": [False, False, True]}]
                                )
                        ]),
                    )
                ])
            st.plotly_chart(dia_hora, use_container_width=True)

with tabs[4]:
    col_met, col_met2 = st.columns(2)
    metodos2 = metodos.groupby('tipo').agg({'monto':'count'}).reset_index()
    metodos3 = metodos.copy()
    metodos3.notaventa = metodos3.notaventa.astype(float)
    merged_df2 = df_rubros.merge(metodos3, on='notaventa', how='inner')
    grouped_df = merged_df2.groupby(['rubro', 'tipo']).size().unstack().reset_index()
    melted_df2 = pd.melt(grouped_df, id_vars='rubro', var_name='tipo', value_name='count')

    grouped_df_barras = merged_df2.groupby(['DIA', 'tipo']).size().unstack().reset_index()
    melted_df_barras = pd.melt(grouped_df_barras, id_vars='DIA', var_name='tipo', value_name='count')
    melted_df_barras['DIA'] = melted_df_barras['DIA'].astype(cat_day_of_week)
    melted_df_barras = melted_df_barras.sort_values(['DIA', 'tipo', 'count'], ascending=True)
    melted_df_barras['DIA'] = melted_df_barras['DIA'].astype(object)

    with col_met:
        st.write("**Distribución de los métodos de pagos**")
        datita_pie = px.pie(metodos2, values='monto', names='tipo')
        datita_pie.update_traces(hovertemplate='Método de pago: %{label}<br>Cantidad transacciones: %{value}')
        st.plotly_chart(datita_pie)
    with col_met2:
        merged_df2_sorted = merged_df2.sort_values('rubro')
        st.write("**Distribución de método de pago según el rubro singular**")
        filtro_rubro = st.selectbox(label = '**Seleccionar un rubro**', 
                    options= merged_df2_sorted.rubro.unique())

        tabla_pie_query = merged_df2_sorted.query('rubro == @filtro_rubro')
        tabla_pie_query = tabla_pie_query.groupby('tipo').agg({'rubro': 'count'}).reset_index()
        datita_pie2 = px.pie(tabla_pie_query, values='rubro', names='tipo')
        datita_pie2.update_traces(textposition='inside', textinfo='percent+label')
        datita_pie2.update_traces(hovertemplate='Método de pago: %{label}<br>Cantidad de transacciones: %{value}')
        st.plotly_chart(datita_pie2)

    barras_tipo_pago = px.bar(melted_df_barras, x='DIA', y='count', color='tipo', barmode='stack', orientation='v', hover_data={'tipo': True})
    barras_tipo_pago.update_layout(legend_title='<br>Tipo de pago<br>', xaxis_title='DIA', yaxis_title='Cantidad', title='Tipos de pago según el día')
    barras_tipo_pago.update_traces(hovertemplate='Método de pago: %{customdata[0]}<br>Cantidad de transacciones: %{y}')
    barras_tipo_pago.update_traces(hoverlabel=dict(namelength=0))
    st.plotly_chart(barras_tipo_pago, use_container_width=True)

