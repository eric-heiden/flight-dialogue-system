var app = angular.module('FIS', []);

app.factory('socket', ['$rootScope', function ($rootScope) {
    var socket = io.connect();

    return {
        on: function (eventName, callback) {
            socket.on(eventName, callback);
        },
        emit: function (eventName, data) {
            socket.emit(eventName, data);
        }
    };
}]);

app.controller('ChatCtrl', function ($scope, $timeout, socket) {
    $scope.chat = [];
    $scope.state = {};
    $scope.progress = undefined;
    socket.on('message', function (data) {
        data.partner = "other";
        data.time = moment().format("HH:mm");
        console.log(data);
        $scope.$apply(function () {
            if (data.type == 'progress')
                $scope.progress = data;
            else {
                $scope.chat.push(data);
                $scope.progress = undefined;
            }
        });
        $timeout(function() {
          window.scrollTo(0,document.body.scrollHeight);
        }, 0, false);
    });
    socket.on('state', function (data) {
        console.log('User state updated', data);
        $scope.$apply(function () {
            for (var key in data) {
                data[key] = data[key].map(function (pair) {
                    return { value: pair[0], score: pair[1].toFixed(3) };
                });
            }
            $scope.state = data;
        });
    });
    $scope.input = "";
    $scope.send = function() {
        socket.emit('message', {"query": $scope.input});
        $scope.chat.push({
            partner: "self",
            time: moment().format("HH:mm"),
            text: $scope.input
        });
        $timeout(function() {
          window.scrollTo(0,document.body.scrollHeight);
        }, 0, false);
        $scope.input = "";
    };
});