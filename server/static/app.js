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
    socket.on('message', function (data) {
        data.partner = "other";
        data.time = moment().format("HH:mm");
        console.log(data);
        $scope.$apply(function () {
            $scope.chat.push(data);
        });
        $timeout(function() {
          window.scrollTo(0,document.body.scrollHeight);
        }, 0, false);
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