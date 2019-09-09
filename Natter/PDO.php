<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

/**
 * Extend PDO with quick utility calls and performance logging.
 **/
class Natter_PDO extends PDO {

    public $last_sh = null;
    public $time_spent = 0;
    public $query_count = 0;

    protected $destruct_callbacks = array();

/**
 * Destructor
 **/
    public function __destruct() {
        $this->runDestructCallbacks();
        // PDO lacks a __destruct:: #parent::__destruct();
        return true;
    } // end __destruct

/**
 * Add a callback to be called during destruction.
 *
 * @param   mixed
 **/
    public function addDestructCallback($callback) {
        $this->destruct_callbacks[] = $callback;
    } // end addDestructCallback

/**
 * Run destructor callbacks
 **/
    function runDestructCallbacks() {
        foreach($this->destruct_callbacks as $callback)
            call_user_func($callback);
        $this->destruct_callbacks = array();
    } // end runDestructCallbacks

/**
 * Perform an SQL query, gathering statistics
 *
 * @param   string
 * @param   array
 *
 * @return  PDO_Statement
 **/
    public function query($sql, $param = null) {
        $this->query_count++;
        $start = microtime(true);
        if(!$param) {
            $sh = parent::query($sql);
        } else {
            if(!is_array($param))
                $param = array( $param );
            $sh = $this->prepare($sql);
            $sh->execute($param);
        } // end if
        $this->time_spent += ( microtime(true) - $start );
        $this->last_sh = $sh;
        return $sh;
    } // end query

/**
 * Perform an SQL query, returning a the first row from the first column
 *
 * @param   string
 * @param   array
 *
 * @return  mixed   String from database, or false if there are no results
 **/
    public function queryOne($sql, $param = null) {
        $sh = $this->query($sql, $param);
        $res = $sh->fetch(PDO::FETCH_NUM);
        $sh->closeCursor();
        //var_export($res);
        if($res && is_array($res))
            return $res[0];
        else
            return false;
    } // end queryOne

/**
 * Perform an SQL query, returning a the first column from all rows
 *
 * @param   string
 * @param   array
 * @param   int
 *
 * @return  array
 **/
    public function queryCol($sql, $param = null, $col = 0) {
        $sh = $this->query($sql, $param);
        $res = array();
        while($row = $sh->fetch(PDO::FETCH_NUM)) {
            $res[] = $row[$col];
        } // end while
        $sh->closeCursor();
        return $res;
    } // end queryCol

/**
 * Perform an SQL query, returning the first two columns from each row as a k=>v pair
 *
 * @param   string
 * @param   array
 *
 * @return  array
 **/
    public function queryPairs($sql, $param = null) {
        $sh = $this->query($sql, $param);
        $res = array();
        while($row = $sh->fetch(PDO::FETCH_NUM)) {
            $res[$row[0]] = $row[1];
        } // end while
        $sh->closeCursor();
        return $res;
    } // end queryPairs


/**
 * Perform an SQL query, returning a the first row as a numbered array
 *
 * @param   string
 * @param   array
 *
 * @return  array
 **/
    public function queryArray($sql, $param = null) {
        $sh = $this->query($sql, $param);
        $res = $sh->fetch(PDO::FETCH_NUM);
        $sh->closeCursor();
        return $res;
    } // end queryArray

/**
 * Perform an SQL query, returning a the first row as an associative array
 *
 * @param   string
 * @param   array
 *
 * @return  array
 **/
    public function queryAssoc($sql, $param = null) {
        $sh = $this->query($sql, $param);
        $res = $sh->fetch(PDO::FETCH_ASSOC);
        $sh->closeCursor();
        return $res;
    } // end queryAssoc

/**
 * Perform an SQL query, returning all rows in an array, each row as a numbered array
 *
 * @param   string
 * @param   array
 *
 * @return  array
 **/
    public function queryAllArray($sql, $param = null) {
        $sh = $this->query($sql, $param);
        $res = $sh->fetchAll(PDO::FETCH_NUM);
        $sh->closeCursor();
        return $res;
    } // end queryAllArray

/**
 * Perform an SQL query, returning all rows in an array, each row as an assocative array
 *
 * @param   string
 * @param   array
 *
 * @return  array
 **/
    public function queryAllAssoc($sql, $param = null) {
        $sh = $this->query($sql, $param);
        $res = $sh->fetchAll(PDO::FETCH_ASSOC);
        $sh->closeCursor();
        return $res;
    } // end queryAllAssoc

/**
 * Perform an SQL query, returning all rows in an associative array, each row as an associative array
 *
 * @param   string
 * @param   array
 * @param   string
 *
 * @return  array
 **/
    public function queryAllAssocKeyed($sql, $param = null, $key = null) {
        if(!$key)
            return false;
        $sh = $this->query($sql, $param);
        $res = array();
        while($row = $sh->fetch(PDO::FETCH_ASSOC)) {
            $res[$row[$key]] = $row;
        } // end while
        $sh->closeCursor();
        return $res;
    } // end queryAllAssocKeyed

} // end Natter_PDO
