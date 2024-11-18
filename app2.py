import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import mpld3
from mpld3 import plugins, utils
import json

class DragPlugin(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", DragPlugin);
    DragPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    DragPlugin.prototype.constructor = DragPlugin;
    DragPlugin.prototype.requiredProps = ["id"];
    DragPlugin.prototype.defaultProps = {}
    function DragPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
        mpld3.insert_css("#" + fig.figid + " path.dragging",
                         {"fill-opacity": "1.0 !important",
                          "stroke-opacity": "1.0 !important"});
    };

    DragPlugin.prototype.draw = function(){
        var obj = mpld3.get_element(this.props.id);
        
        var div = d3.select("#coords-info");
        if (div.empty()) {
            div = d3.select("body").append("div")
                    .attr("id", "coords-info")
                    .style("padding", "10px")
                    .style("background", "white")
                    .style("border", "1px solid black")
                    .style("margin", "10px");
        }

        var drag = d3.drag()
            .subject(function(d) { return {x:obj.ax.x(d[0]),
                                          y:obj.ax.y(d[1])}; })
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);

        obj.elements()
           .data(obj.offsets)
           .style("cursor", "default")
           .call(drag);

        function dragstarted(d, i) {
            d3.event.sourceEvent.stopPropagation();
            d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
            d[0] = obj.ax.x.invert(d3.event.x);
            d[1] = obj.ax.y.invert(d3.event.y);
            d3.select(this)
              .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
            
            // Update coordinates display
            div.html("Point " + i + ": (" + d[0].toFixed(2) + ", " + d[1].toFixed(2) + ")");
        }

        function dragended(d, i) {
            d3.select(this).classed("dragging", false);
            // Prepare the data to send
            var coordinates = {
                index: i,
                x: d[0],
                y: d[1]
            };
            
            // Update display
            div.html("Final - Point " + i + ": (" + d[0].toFixed(2) + ", " + d[1].toFixed(2) + ")");
            
            // Send data to Streamlit
            window.Streamlit.setComponentValue(coordinates);
        }
    }
    """

    def __init__(self, points):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                     "id": utils.get_id(points, suffix)}

# Initialize session state for storing point coordinates
if 'point_history' not in st.session_state:
    st.session_state.point_history = []

if 'current_points' not in st.session_state:
    # Initialize with random points
    st.session_state.current_points = np.random.normal(size=(20, 2))

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))
points = ax.plot(st.session_state.current_points[:, 0], 
                st.session_state.current_points[:, 1], 
                'or', alpha=0.5, markersize=50, markeredgewidth=1)
ax.set_title("Click and Drag Points", fontsize=18)
ax.grid(True)

# Connect the plugin
plugins.connect(fig, DragPlugin(points[0]))

# Create columns for the layout
col1, col2 = st.columns([2, 1])

with col1:
    # Display the plot
    component_value = st.components.v1.html(mpld3.fig_to_html(fig), height=600)
    
    # Handle the component value
    if component_value and isinstance(component_value, dict):
        # Add to history
        st.session_state.point_history.append(component_value)
        
        # Update current points
        idx = component_value['index']
        st.session_state.current_points[idx] = [component_value['x'], component_value['y']]
        st.experimental_rerun()  # Refresh the plot with new coordinates

with col2:
    # Display current coordinates
    st.write("### Current Points Coordinates")
    for i, point in enumerate(st.session_state.current_points):
        st.write(f"Point {i}: ({point[0]:.2f}, {point[1]:.2f})")
    
    # Display movement history
    if st.session_state.point_history:
        st.write("### Recent Movements")
        for move in st.session_state.point_history[-5:]:  # Show last 5 movements
            st.write(f"Point {move['index']}: ({move['x']:.2f}, {move['y']:.2f})")

    # Add a button to clear history
    if st.button("Clear History"):
        st.session_state.point_history = []
        st.experimental_rerun()

# Add a button to get current coordinates
if st.button("Get Current Coordinates"):
    st.write("### All Point Coordinates")
    st.json(st.session_state.current_points.tolist())