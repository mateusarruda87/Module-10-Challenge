# Import dependencies
import numpy as np
import pandas as pd
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the table
measurement = Base.classes.measurement
station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List of all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/preciptation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date_(YYYY-MM-DD)<br/>"
        f"/api/v1.0/start_date_(YYYY-MM-DD)/end_date_(YYYY-MM-DD)"
    )

# Returns json with the date as the key and the value as the precipitation
# Only returns the jsonified precipitation data for the last year in the database
@app.route("/api/v1.0/preciptation")
def precipitation():
    session = Session(engine)

    # Find the most recent date in the data set.
    most_recent_date = session.query(func.max(measurement.date)).scalar()
    most_recent_date
    
    # Calculate date from a year before most recent date
    date_f = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') 
    date_i = date_f - dt.timedelta(days=366)

    # Query last year of precipitation data
    preciptation = session.query(measurement.date, measurement.prcp).filter(measurement.date >= date_i)

    session.close()

    # Add data to dictionary
    prcp_last_year = []
    for date, prec in preciptation:
        prcp_dict = {}
        prcp_dict[date] = prec
        prcp_last_year.append(prcp_dict)
    
    return jsonify(prcp_last_year)


# Returns jsonified data of all of the stations in the database
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)

    # Query all stations
    results = session.query(station.station, station.name, station.latitude, station. longitude, station.elevation)

    session.close()

    # Add data to a dictionary
    all_stations = []
    
    for id, stat, lat, lng, elv in results:
        sta_dict = {}
        sta_dict['id'] = id
        sta_dict['station'] = stat
        sta_dict['latitude'] = lat
        sta_dict['longitude'] = lng
        sta_dict['elevation'] = elv
        all_stations.append(sta_dict)
    
    return jsonify(all_stations)


# Returns jsonified data for the most active station
# Only returns the jsonified data for the last year of data
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    # Find the most recent date in the data set.
    date_f = session.query(func.max(measurement.date)).scalar()

    # Calculate date from a year before most recent date
    date_i = dt.datetime.strptime(date_f, '%Y-%m-%d') - dt.timedelta(days=366)

    # Design a query to find the most active stations
    stations_count = session.query(measurement.station, func.count(measurement.station)).\
                     group_by(measurement.station).order_by(desc(func.count(measurement.station))).all()

    # Select most active stations
    most_active = stations_count[0][0]

    # Query temperature data for most active station
    results = session.query(measurement.tobs, measurement.date).filter(measurement.station == most_active).filter(measurement.date >= date_i).all()
    
    session.close()

    # Add data to dictionary
    temperatures = []
    for tob, dat in results:
        tob_dict = {}
        tob_dict[dat] = tob
        temperatures.append(tob_dict)

    return jsonify(temperatures)


# Accepts the start date as a parameter from the URL
# Returns the min, max, and average temperatures calculated from the given start date to the end of the dataset 
@app.route("/api/v1.0/<start>")
def start(start):
    session = Session(engine)

    # Filter temperature data by user-specified date and calculate summary statistics
    results = session.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).filter(measurement.date >= start).all()

    # Add summary statistics to a dictionary
    temp_stats = []
    for min, max, avg in results:
        stats_dict = {}
        stats_dict['min temp'] = min
        stats_dict['max temp'] = max
        stats_dict['average temp'] = avg
        temp_stats.append(stats_dict)
    
    return jsonify(temp_stats)


# Accepts the start and end dates as parameters from the URL
# Returns the min, max, and average temperatures calculated from the given start date to the given end date
@app.route("/api/v1.0/<start>/<end>")
def startend(start, end):
    session = Session(engine)

    # Filter temperature data by user-specified date and calculate summary statistics
    results = session.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).filter(measurement.date >= start).filter(measurement.date <= end).all()

    # Add summary statistics to a dictionary
    temp_stats = []
    for min, max, avg in results:
        stats_dict = {}
        stats_dict['min temp'] = min
        stats_dict['max temp'] = max
        stats_dict['average temp'] = avg
        temp_stats.append(stats_dict)
    
    return jsonify(temp_stats)


if __name__ == '__main__':
    app.run(debug=True)