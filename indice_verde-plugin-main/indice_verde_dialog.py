# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IndiceVerdeDialog
                                 A QGIS plugin
 Indices Vegetativos
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-10-24
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Caio Arantes
        email                : github.com/caioarantes
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import platform
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
import ee
import geopandas as gpd
import requests
from qgis.core import QgsRasterLayer, QgsProject,QgsMapLayer



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'indice_verde_dialog_base.ui'))


class IndiceVerdeDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(IndiceVerdeDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.autenticacao.clicked.connect(self.auth)
        self.autenticacao_teste.clicked.connect(self.auth_test)
        self.desautenticacao.clicked.connect(self.auth_clear)
        self.getdates.clicked.connect(self.run1_clicked)
        self.update_vector.clicked.connect(self.update_vector_clicked)
        self.getpath.clicked.connect(self.get_layer_path_from_combobox)
        self.load_vector.clicked.connect(self.load_vector_function)
        self.load_1ndvi.clicked.connect(self.first_ndvi)
        self.load_allndvi.clicked.connect(self.all_ndvi_function)
        self.load_mediandvi.clicked.connect(self.mean_ndvi)
        self.clear_raster.clicked.connect(self.clear_all_raster_layers)

        self.inicio  = None 
        self.final = None
        self.nuvem = None
        self.vector_path = None
        self.aoi = None

    def auth(self):
        print('Autenticando...')
        ee.Authenticate()    

    def auth_test(self):
    # Attempt to initialize Earth Engine
        try:
            ee.Initialize()
            self.pop_aviso("Autenticação bem-sucedida!")
            print("Authentication successful!")

        except ee.EEException as e:
            if "Earth Engine client library not initialized" in str(e):
                self.pop_aviso("Falha na autenticação. Por favor, autentique-se.")
                print("Authentication failed. Please authenticate.")
                ee.Authenticate()
                ee.Initialize()  # Retry after authentication
            else:
                print(f"An error occurred: {e}")


    def auth_clear(self):
        print('Desautenticando...')
        """Clears the Earth Engine authentication by deleting the credentials file."""
        
        system = platform.system()
        
        # Set the path for Earth Engine credentials based on the operating system
        if system == 'Windows':
            credentials_path = os.path.join(os.environ['USERPROFILE'], '.config', 'earthengine', 'credentials')
        elif system == 'Linux':
            credentials_path = os.path.join(os.environ['HOME'], '.config', 'earthengine', 'credentials')
        elif system == 'Darwin':  # MacOS
            credentials_path = os.path.join(os.environ['HOME'], 'Library', 'Application Support', 'earthengine', 'credentials')
        else:
            raise Exception(f"Unsupported operating system: {system}")

        # Check if the credentials file exists and delete it
        if os.path.exists(credentials_path):
            os.remove(credentials_path)
            self.pop_aviso("Autenticação do Earth Engine limpa com sucesso")
            print("Earth Engine authentication cleared successfully.")
        else:
            self.pop_aviso("Nenhuma credencial do Earth Engine encontrada para limpar.")
            print("No Earth Engine credentials found to clear.")

    def run1_clicked(self):
        # Get the date from the QDateEdit widget
        self.inicio = self.incioedit.date().toString("yyyy-MM-dd")

        self.final = self.finaledit.date().toString("yyyy-MM-dd")
        print(f"Selected date: {self.inicio} to {self.final}")

        # Get the selected text from the combobox
        self.nuvem = int(self.nuvemcombo.currentText().split('%')[0])
        print(f"Nuvem limit: {self.nuvem}")




    def pop_aviso(self, aviso):
        QApplication.restoreOverrideCursor()
        msg = QMessageBox(parent=self)
        msg.setWindowTitle("Alerta!")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(aviso)
        msg.exec_()

    def update_vector_clicked(self):
        self.comboBox.clear()

        # Get the list of all layers in the current QGIS project
        layers = QgsProject.instance().layerTreeRoot().children()

        # Iterate through the layers and add vector layer names to the ComboBox
        for layer in layers:
            if layer.layer().type() == QgsMapLayer.VectorLayer:  # Check if it's a vector layer
                self.comboBox.addItem(layer.layer().name())

        # Optional: Set the first item as the current selection
        if self.comboBox.count() > 0:
            self.comboBox.setCurrentIndex(0)



    def get_layer_path_from_combobox(self):
        """
        Gets the current text from the ComboBox, finds the corresponding
        layer, and retrieves its shapefile path.

        Parameters:
        combo_box (QComboBox): The ComboBox containing layer names.

        Returns:
        str: The file path of the shapefile, or None if not found.
        """
        # Get the current layer name from the ComboBox
        layer_name = self.comboBox.currentText()
        
        # Find the layer in the current QGIS project by name
        layer = QgsProject.instance().mapLayersByName(layer_name)
        
        # Check if the layer exists and is a vector layer
        if layer:
            vector_layer = layer[0]  # Get the first layer with that name
            if vector_layer.type() == QgsMapLayer.VectorLayer:
                # Get the path of the vector layer
                layer_path = vector_layer.dataProvider().dataSourceUri()
                # Check if it's a shapefile and return the path
                if layer_path.lower().endswith('.shp'):
                    self.vector_path = layer_path
                    print(layer_path)
                else:
                    print("The selected layer is not a shapefile.")
            else:
                print("The selected layer is not a vector layer.")
        else:
            print("Layer not found.")

    def load_vector_function(self):
        shapefile_path = self.vector_path
        gdf = gpd.read_file(shapefile_path)

        # Check if there is at least one geometry in the GeoDataFrame
        if not gdf.empty:
            # If the GeoDataFrame contains multiple geometries, dissolve them into one
            if len(gdf) > 1:
                self.aoi = gdf.dissolve()
            else:
                self.aoi = gdf

            # Extract the first geometry from the dissolved GeoDataFrame
            geometry = self.aoi.geometry.iloc[0]

            # Check if the geometry is a Polygon or MultiPolygon
            if geometry.geom_type in ['Polygon', 'MultiPolygon']:
                # Convert the geometry to GeoJSON format
                geojson = geometry.__geo_interface__

                # Remove the third dimension from the coordinates
                if geojson['type'] == 'Polygon':
                    geojson['coordinates'] = [list(map(lambda coord: coord[:2], ring)) for ring in geojson['coordinates']]
                elif geojson['type'] == 'MultiPolygon':
                    geojson['coordinates'] = [[list(map(lambda coord: coord[:2], ring)) for ring in polygon] for polygon in geojson['coordinates']]

                # Create an Earth Engine geometry object from the GeoJSON coordinates
                ee_geometry = ee.Geometry(geojson)

                # Convert the Earth Engine geometry to a Feature
                feature = ee.Feature(ee_geometry)

                # Create a FeatureCollection with the feature
                self.aoi = ee.FeatureCollection([feature])

                print("AOI defined successfully.")
            else:
                print("The geometry is not a valid type (Polygon or MultiPolygon).")
        else:
            print("The shapefile does not contain any geometries.")

    def first_ndvi(self):
        # Initialize Earth Engine
        ee.Initialize()

        aoi = self.aoi
            
        startDate = self.inicio
        endDate = self.final

        # Access Sentinel-2 ImageCollection and get the first image
        sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(startDate, endDate) \
            .filterBounds(aoi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

        # Get the first image from the collection
        first_image = ee.Image(sentinel2.first())

        # Calculate NDVI: (NIR - Red) / (NIR + Red)
        ndvi = first_image.normalizedDifference(['B8', 'B4']).rename('NDVI')

        # Calculate EVI: 2.5 * (NIR - Red) / (NIR + 6 * Red - 7.5 * Blue + 1)
        # evi = first_image.expression(
        #     '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        #     {
        #     'NIR': first_image.select('B8'),
        #     'RED': first_image.select('B4'),
        #     'BLUE': first_image.select('B2')
        #     }
        # ).rename('EVI')

        # # Determine whether to use NDVI or EVI based on the ComboBox selection
        # index_type = self.index_type_combo.currentText()

        # if index_type == 'NDVI':
        #     selected_index = ndvi
        #     index_name = 'NDVI'
        # elif index_type == 'EVI':
        #     selected_index = evi
        #     index_name = 'EVI'
        # else:
        #     print("Invalid index type selected.")
        #     return

        # Extract the acquisition date of the image
        date = ee.Date(first_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()

        # Generate the download URL for the NDVI image
        url = ndvi.getDownloadUrl({
            'scale': 10,  # 10 meters for Sentinel-2 data
            'region': aoi.geometry().bounds().getInfo(),  # The region of interest
            'format': 'GeoTIFF'  # Specify the format to download
        })

        # Download the NDVI image
        output_file = f'NDVI_{date}.tif'
        response = requests.get(url)
        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"NDVI image downloaded as {output_file}")

        # Load the downloaded NDVI GeoTIFF into QGIS
        layer_name = f'NDVI {date}'  # Layer name with acquisition date
        raster_layer = QgsRasterLayer(output_file, layer_name)

        if raster_layer.isValid():
            QgsProject.instance().addMapLayer(raster_layer)
            print(f"NDVI layer loaded into QGIS successfully with layer name '{layer_name}'!")
        else:
            print("Failed to load NDVI layer into QGIS.")

    def all_ndvi_function(self):
        # Initialize Earth Engine if not already initialized
        ee.Initialize()

        aoi = self.aoi
        startDate = self.inicio
        endDate = self.final

        # Access Sentinel-2 ImageCollection and filter based on date and area of interest
        sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(startDate, endDate) \
            .filterBounds(aoi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))


        # Get the number of images in the collection
        num_images = sentinel2.size().getInfo()
        print(f"Number of images in the collection: {num_images}")
        self.pop_aviso(f"Numero de imagens da coleção: {num_images}")

        # Get a list of all images in the collection
        image_list = sentinel2.toList(num_images)

        # Loop through each image to print the date
        for i in range(num_images):
            # Access each image
            image = ee.Image(image_list.get(i))
            
            # Extract and print the acquisition date
            date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
            print(f"Image {i + 1} date: {date}")

            # (Optional) Continue processing each image as needed
            # E.g., calculate NDVI and download, as in previous code

        # Loop through each image in the collection
        for i in range(image_list.size().getInfo()):
            first_image = ee.Image(image_list.get(i))

            # Calculate NDVI: (NIR - Red) / (NIR + Red)
            ndvi = first_image.normalizedDifference(['B8', 'B4']).rename('NDVI')

            # Extract the acquisition date of the image
            date = ee.Date(first_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()

            # Generate the download URL for the NDVI image
            url = ndvi.getDownloadUrl({
                'scale': 10,  # 10 meters for Sentinel-2 data
                'region': aoi.geometry().bounds().getInfo(),  # The region of interest
                'format': 'GeoTIFF'  # Specify the format to download
            })

            # Download the NDVI image
            output_file = f'NDVI_{date}.tif'
            response = requests.get(url)
            with open(output_file, 'wb') as f:
                f.write(response.content)

            print(f"NDVI image downloaded as {output_file}")

            # Load the downloaded NDVI GeoTIFF into QGIS
            layer_name = f'NDVI {date}'  # Layer name with acquisition date
            raster_layer = QgsRasterLayer(output_file, layer_name)

            if raster_layer.isValid():
                QgsProject.instance().addMapLayer(raster_layer)
                print(f"NDVI layer loaded into QGIS successfully with layer name '{layer_name}'!")
            else:
                print("Failed to load NDVI layer into QGIS.")

    def mean_ndvi(self):
        # Initialize Earth Engine if not already initialized
        ee.Initialize()

        aoi = self.aoi
        startDate = self.inicio
        endDate = self.final

        # Access Sentinel-2 ImageCollection and filter based on date and area of interest
        sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(startDate, endDate) \
            .filterBounds(aoi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

        # Calculate the mean image from the filtered collection
        mean_image = sentinel2.mean()

        # Calculate NDVI: (NIR - Red) / (NIR + Red) for the mean image
        mean_ndvi = mean_image.normalizedDifference(['B8', 'B4']).rename('NDVI')

        # Generate the download URL for the mean NDVI image
        url = mean_ndvi.getDownloadUrl({
            'scale': 10,  # 10 meters for Sentinel-2 data
            'region': aoi.geometry().bounds().getInfo(),  # The region of interest
            'format': 'GeoTIFF'  # Specify the format to download
        })

        # Download the mean NDVI image
        output_file = f'Mean_NDVI.tif'
        response = requests.get(url)
        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"Mean NDVI image downloaded as {output_file}")

        # Load the downloaded mean NDVI GeoTIFF into QGIS
        layer_name = f'Mean NDVI'  # Layer name with acquisition date
        raster_layer = QgsRasterLayer(output_file, layer_name)

        if raster_layer.isValid():
            QgsProject.instance().addMapLayer(raster_layer)
            print(f"Mean NDVI layer loaded into QGIS successfully with layer name '{layer_name}'!")
        else:
            print("Failed to load Mean NDVI layer into QGIS.")

    def clear_all_raster_layers(self):
        # Get the current project instance
        project = QgsProject.instance()
        
        # Iterate over all layers in the project
        for layer in project.mapLayers().values():
            # Check if the layer is a raster layer
            if layer.type() == QgsMapLayer.RasterLayer:
                # Remove the layer from the project
                project.removeMapLayer(layer)
                print(f"Removed raster layer: {layer.name()}")

        print("All raster layers have been cleared.")