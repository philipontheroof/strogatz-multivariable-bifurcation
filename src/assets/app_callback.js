if (!window.dash_clientside) {
    window.dash_clientside = {};
}

function rk4_one_step(f, x, t, dt) {
    var k1 = dt * f(t, x);
    var k2 = dt * f(t + dt / 2, x + k1 / 2);
    var k3 = dt * f(t + dt / 2, x + k2 / 2);
    var k4 = dt * f(t + dt, x + k3);

    var newX = x + (k1 + 2 * k2 + 2 * k3 + k4) / 6;
    var newT = t + dt;

    return [newT, newX];
}

function func(t, x, r, h) {
    return r * x - x * x * x + h;
}

function linspace(start, stop, num) {
    var step = (stop - start) / (num - 1);
    var arr = new Array(num);
    for (var i = 0; i < num; i++) {
        arr[i] = start + step * i;
    }
    return arr;
}


let initial_x = 0;
let initial_t = 0;
let x = initial_x;
let t = initial_t;
let dt = 1 / 60;
let n = 1;
let fx = linspace(-5, 5, 100);
let is_noise_active = false;



window.dash_clientside.clientside = {
    update_noise_button_label: function (n_clicks) {
        if (n_clicks % 2 === 0) {
            is_noise_active = false;
            return "Add Noise";
        } else {
            is_noise_active = true;
            return "Remove Noise";
        }
    },

    update_graph: function (interval, r, h, noise_clicks, reset_clicks, figure) {
        var relayout_data = figure.layout;
        var data = figure.data;

        function f(t, x) {
            return func(t, x, r, h);
        }

        var fy = fx.map(x => f(0, x));
        for (var i = 0; i < n; i++) {
            var rk4_result = rk4_one_step(f, x, t, dt / n);
            t = rk4_result[0];
            x = rk4_result[1];
        }

        if (is_noise_active) {
            x += (Math.random() * 0.005) - 0.0025; // Add noise centered around 0
        }

        if (!relayout_data['title']) {
            relayout_data['title'] = {};
        }
        relayout_data['title']['text'] = "t=" + t.toFixed(2);

        // Update the existing data points
        data[1]['x'] = fx;
        data[1]['y'] = fy;
        data[2]['x'] = [x];
        data[2]['y'] = [0];

        return {
            "layout": relayout_data,
            "data": data,
        };
    },

    reset_simulation: function (n_clicks) {
        if (n_clicks > 0) {
            x = initial_x;
            t = initial_t;
            return 0;
        }
    }
};
