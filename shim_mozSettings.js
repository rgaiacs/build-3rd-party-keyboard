/**
 * Copyright 2014, Salvador de la Puente González
 * salva@unoyunodiez.com
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {

/**
 * The library provides a shim for mozSettings taking advantage of the
 * `storage` event which is broadcasted across all the windows with the same
 * origin allowing to emulate `addObserver` method.
 */

  'use strict';

  var window = this;

  var activeLocks = [];
  var observers = {};

  window.addEventListener('storage', function (evt) {
    tellObservers(evt.key, evt.newValue);
  });

  function Lock() {
    this._requests = [];
    this.closed = false;
  }

  Lock.prototype.set = function (updates) {
    var newDOMRequest = {};
    this._requests.push(['set', newDOMRequest, updates]);
    return newDOMRequest;
  };

  Lock.prototype.get = function (key) {
    var newDOMRequest = {};
    this._requests.push(['get', newDOMRequest, key]);
    return newDOMRequest;
  };

  Lock.prototype._execute = function (callback) {
    if (this._requests.length === 0) { callback(); return; }
    nextRequest.call(this);

    function nextRequest() {
      if (this._requests.length === 0) { callback(); return; }

      var request = this._requests[0];
      var type = request[0];
      var domRequest = request[1];
      var data = request[2];
      this._process(type, domRequest, data, function () {
        this._requests.shift();
        nextRequest.call(this);
      }.bind(this));
    }
  };

  Lock.prototype._process = function (type, domRequest, data, callback) {
    this._operations[type].call(this, domRequest, data, callback);
  };

  Lock.prototype._operations = {
    'get': function operationGet(domRequest, key, callback) {
      get(key, function onValue(value) {
        domRequest.result = {};
        domRequest.result[key] = value;
        domRequest.onsuccess && domRequest.onsuccess();
        callback && callback();
      });
    },

    'set': function operationSet(domRequest, updates, callback) {
      var settingsToUpdate = Object.keys(updates);
      var sync = waitFor(settingsToUpdate.length, function onAllUpdated() {
        domRequest.onsuccess && domRequest.onsuccess();
        callback && callback();
      });
      settingsToUpdate.forEach(function updateOneSetting(settingName) {
        set(settingName, updates[settingName], sync);
      });
    }
  };

  window.navigator.mozSettings = {
    createLock: function () {
      var newLock = new Lock();
      activeLocks.push(newLock);
      setTimeout(processNextLock, 0);
      return newLock;
    },

    addObserver: function (settingName, handler) {
      if (!observers.hasOwnProperty(settingName)) {
        observers[settingName] = [];
      }
      var settingObservers = observers[settingName];
      if (settingObservers.indexOf(handler) < 0) {
        settingObservers.push(handler);
      }
    },

    removeObserver: function (settingName, handler) {
      if (!observers.hasOwnProperty(settingName)) { return; }
      var settingObservers = observers[settingName];
      settingObservers.splice(settingObservers.indexOf(handler), 1);
    }
  };

  function tellObservers(settingName, value) {
    var evt = {};
    evt.settingName = settingName;
    evt.settingValue = value;
    (window.navigator.mozSettings.onsettingchange &&
     window.navigator.mozSettings.onsettingchange(evt));
    var settingObservers = observers[settingName] || [];
    settingObservers.forEach(function dispatchEvent(handler) {
      handler(evt);
    });
  };

  function processNextLock(callback) {
    if (activeLocks.length === 0) { callback && callback(); return; }
    if (activeLocks.length > 1) { return; }

    var lock = activeLocks[0];
    lock._execute.call(lock, function then() {
      lock.closed = true;
      activeLocks.shift();
      setTimeout(processNextLock, 0, callback);
    });
  }

  function waitFor(pending, callback) {
    return function () {
      pending--;
      if (!pending) { callback(); }
    };
  }

  function set(key, value, callback) {
    setTimeout(function fakedAsyncSet(representation) {
      window.localStorage.setItem(key, representation);
      callback();
    }, 0, JSON.stringify(value));
  }

  function get(key, callback) {
    setTimeout(function fakedAsyncGet() {
      var representation = window.localStorage.getItem(key);
      callback(representation && JSON.parse(representation));
    }, 0);
  }

}.call(this));
