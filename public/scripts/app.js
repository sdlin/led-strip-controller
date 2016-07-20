var Gauge = React.createClass({
  handleOnInput: function(event) {
    this.setState(this.makeState(event.target.value));
    this.props.onValueUpdate(event.target.value);
  },

  getInitialState: function() {
    return this.makeState(this.props.colorVal)
  },

  makeState: function(value) {
    return {currentValue: value}
  },

  render: function() {
    return (
      <div className="Gauge">
        <input type="range" min="0" max="255" step="1" defaultValue={this.state.currentValue} onInput={this.handleOnInput}></input>
        <span className="valueDisplay">
          {this.state.currentValue}
        </span>
      </div>
    );
  }
});


var RgbControl = React.createClass({
  getInitialState: function() {
    return this.makeState(0, 0, 0)
  },

  componentWillMount: function() {
    $.ajax({
      url: this.props.url,
      dataType: 'json',
      type: 'GET',
      async: false,
      success: function(data) {
        this.setState(this.makeState(data['r'], data['g'], data['b']));
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },

  makeState: function(r, g, b) {
    return {r: r, g: g, b: b}
  },

  handleGaugeUpdateR: function(value) {
    var newState = this.makeState(value, this.state.g, this.state.b);
    this.setState(newState);
    this.handleRgbUpdate(newState);
  },

  handleGaugeUpdateG: function(value) {
    var newState = this.makeState(this.state.r, value, this.state.b);
    this.setState(newState);
    this.handleRgbUpdate(newState);
  },

  handleGaugeUpdateB: function(value) {
    var newState = this.makeState(this.state.r, this.state.g, value);
    this.setState(newState);
    this.handleRgbUpdate(newState);
  },

  handleRgbUpdate: function(data) {
    $.ajax({
      url: this.props.url,
      dataType: 'json',
      type: 'PUT',
      data: data,
      success: function(data) {
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },

  render: function() {
    return (
      <div className="RgbControl">
        <div className="R">
          <Gauge onValueUpdate={this.handleGaugeUpdateR} colorVal={this.state['r']} />
        </div>
        <div className="G">
          <Gauge onValueUpdate={this.handleGaugeUpdateG} colorVal={this.state['g']} />
        </div>
        <div className="B">
          <Gauge onValueUpdate={this.handleGaugeUpdateB} colorVal={this.state['b']} />
        </div>
      </div>
    );
  }
});


ReactDOM.render(
  <RgbControl url='/api/rgb'/>,
  document.getElementById('content')
);
